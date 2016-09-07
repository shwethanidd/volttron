# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2015, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of the FreeBSD
# Project.
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization that
# has cooperated in the development of these materials, makes any
# warranty, express or implied, or assumes any legal liability or
# responsibility for the accuracy, completeness, or usefulness or any
# information, apparatus, product, software, or process disclosed, or
# represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does not
# necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#}}}

from __future__ import absolute_import

from base64 import b64encode, b64decode
import inspect
import logging
import os
import random
import re
import weakref

import gevent
from gevent.event import AsyncResult
from volttron.platform.agent.utils import get_aware_utc_now

from zmq import green as zmq
from zmq import SNDMORE
from zmq.utils import jsonapi

from .base import SubsystemBase
from ..decorators import annotate, annotations, dualmethod, spawn
from ..errors import Unreachable
from .... import jsonrpc
from volttron.platform.agent import utils
from gevent.queue import Queue, Empty


__all__ = ['PubSub']
min_compatible_version = '3.0'
max_compatible_version = ''

#utils.setup_logging()
_log = logging.getLogger(__name__)

def encode_peer(peer):
    if peer.startswith('\x00'):
        return peer[:1] + b64encode(peer[1:])
    return peer

def decode_peer(peer):
    if peer.startswith('\x00'):
        return peer[:1] + b64decode(peer[1:])
    return peer

class SubsriptionError(StandardError):
    pass

class PubSub(SubsystemBase):
    def __init__(self, core, rpc_subsys, peerlist_subsys, owner, publish_address, subscribe_address):
        self.core = weakref.ref(core)
        self.rpc = weakref.ref(rpc_subsys)
        self.peerlist = weakref.ref(peerlist_subsys)
        self._peer_subscriptions = {}
        self._my_subscriptions = {}
        self._my_ext_subscriptions = {}
        self.protected_topics = ProtectedPubSubTopics()

        self.pubsub_external = PubSubExt(self)

        def setup(sender, **kwargs):
            # pylint: disable=unused-argument
            rpc_subsys.export(self._peer_sync, 'pubsub.sync')
            rpc_subsys.export(self._peer_subscribe, 'pubsub.subscribe')
            rpc_subsys.export(self._peer_unsubscribe, 'pubsub.unsubscribe')
            rpc_subsys.export(self._peer_list, 'pubsub.list')
            rpc_subsys.export(self._peer_publish, 'pubsub.publish')
            rpc_subsys.export(self._peer_push, 'pubsub.push')
            rpc_subsys.export(self._peer_get_external_message, 'get_sub_external_message')

            core.onconnected.connect(self._connected)
            core.onviperror.connect(self._viperror)
            peerlist_subsys.onadd.connect(self._peer_add)

            peerlist_subsys.ondrop.connect(self._peer_drop)

            def subscribe(member):   # pylint: disable=redefined-outer-name
                for peer, bus, prefix in annotations(
                        member, set, 'pubsub.subscriptions'):
                    # XXX: needs updated in light of onconnected signal
                    if self.pubsub_external.is_external(prefix):
                        self.add_ext_subscription(prefix, member)
                    self.add_subscription(peer, prefix, member, bus)
            inspect.getmembers(owner, subscribe)
        core.onsetup.connect(setup, self)

    def add_bus(self, name):
        self._peer_subscriptions.setdefault(name, {})

    def remove_bus(self, name):
        del self._peer_subscriptions[name]
        # XXX: notify subscribers of removed bus
        #      or disallow removal of non-empty bus?

    def _connected(self, sender, **kwargs):
        self.synchronize(None)

    def _viperror(self, sender, error, **kwargs):
        if isinstance(error, Unreachable):
            self._peer_drop(self, error.peer)

    def _peer_add(self, sender, peer, **kwargs):
        # Delay sync by some random amount to prevent reply storm.
        delay = random.random()
        self.core().spawn_later(delay, self.synchronize, peer)

    def _peer_drop(self, sender, peer, **kwargs):
        self._sync(peer, {})

    def _sync(self, peer, items):
        items = {(bus, prefix) for bus, topics in items.iteritems()
                 for prefix in topics}
        remove = []
        for bus, subscriptions in self._peer_subscriptions.iteritems():
            for prefix, subscribers in subscriptions.iteritems():
                item = bus, prefix
                try:
                    items.remove(item)
                except KeyError:
                    subscribers.discard(peer)
                    if not subscribers:
                        remove.append(item)
                else:
                    subscribers.add(peer)
        for bus, prefix in remove:
            subscriptions = self._peer_subscriptions[bus]
            assert not subscriptions.pop(prefix)
        for bus, prefix in items:
            self._add_peer_subscription(peer, bus, prefix)

    def _peer_sync(self, items):
        peer = bytes(self.rpc().context.vip_message.peer)
        assert isinstance(items, dict)
        self._sync(peer, items)

    def _add_peer_subscription(self, peer, bus, prefix):
        subscriptions = self._peer_subscriptions[bus]
        try:
            subscribers = subscriptions[prefix]
        except KeyError:
            subscriptions[prefix] = subscribers = set()
        subscribers.add(peer)

    def _peer_subscribe(self, prefix, bus=''):
        peer = bytes(self.rpc().context.vip_message.peer)
        for prefix in prefix if isinstance(prefix, list) else [prefix]:
            self._add_peer_subscription(peer, bus, prefix)

    def _peer_unsubscribe(self, prefix, bus=''):
        peer = bytes(self.rpc().context.vip_message.peer)
        subscriptions = self._peer_subscriptions[bus]
        if prefix is None:
            remove = []
            for topic, subscribers in subscriptions.iteritems():
                subscribers.discard(peer)
                if not subscribers:
                    remove.append(topic)
            for topic in remove:
                del subscriptions[topic]
        else:
            for prefix in prefix if isinstance(prefix, list) else [prefix]:
                subscribers = subscriptions[prefix]
                subscribers.discard(peer)
                if not subscribers:
                    del subscriptions[prefix]

    def _peer_list(self, prefix='', bus='', subscribed=True, reverse=False):
        peer = bytes(self.rpc().context.vip_message.peer)
        if bus is None:
            buses = self._peer_subscriptions.iteritems()
        else:
            buses = [(bus, self._peer_subscriptions[bus])]
        if reverse:
            test = prefix.startswith
        else:
            test = lambda t: t.startswith(prefix)
        results = []
        for bus, subscriptions in buses:
            for topic, subscribers in subscriptions.iteritems():
                if test(topic):
                    member = peer in subscribers
                    if not subscribed or member:
                        results.append((bus, topic, member))
        return results

    def _peer_publish(self, topic, headers, message=None, bus=''):
        peer = bytes(self.rpc().context.vip_message.peer)
        self._distribute(peer, topic, headers, message, bus)

    def _distribute(self, peer, topic, headers, message=None, bus=''):
        self._check_if_protected_topic(topic)
        subscriptions = self._peer_subscriptions[bus]
        subscribers = set()
        for prefix, subscription in subscriptions.iteritems():
            if subscription and topic.startswith(prefix):
                subscribers |= subscription
        if subscribers:
            sender = encode_peer(peer)
            json_msg = jsonapi.dumps(jsonrpc.json_method(
                None, 'pubsub.push',
                [sender, bus, topic, headers, message], None))
            frames = [zmq.Frame(b''), zmq.Frame(b''),
                      zmq.Frame(b'RPC'), zmq.Frame(json_msg)]
            socket = self.core().socket
            for subscriber in subscribers:
                socket.send(subscriber, flags=SNDMORE)
                socket.send_multipart(frames, copy=False)
        return len(subscribers)

    def _peer_push(self, sender, bus, topic, headers, message):
        '''Handle incoming subscription pushes from peers.'''

        peer = bytes(self.rpc().context.vip_message.peer)
        handled = 0
        try:
            subscriptions = self._my_subscriptions[peer][bus]
        except KeyError:
            pass
        else:
            sender = decode_peer(sender)
            for prefix, callbacks in subscriptions.iteritems():
                if topic.startswith(prefix):
                    handled += 1
                    for callback in callbacks:
                        callback(peer, sender, bus, topic, headers, message)
        if not handled:
            # No callbacks for topic; synchronize with sender
            self.synchronize(peer)

    def synchronize(self, peer):
        '''Unsubscribe from stale/forgotten/unsolicited subscriptions.'''

        if peer is None:
            items = [(peer, {bus: subscriptions.keys()
                             for bus, subscriptions in buses.iteritems()})
                     for peer, buses in self._my_subscriptions.iteritems()]
        else:
            buses = self._my_subscriptions.get(peer) or {}
            items = [(peer, {bus: subscriptions.keys()
                             for bus, subscriptions in buses.iteritems()})]
        for (peer, subscriptions) in items:
            self.rpc().notify(peer, 'pubsub.sync', subscriptions)

    def list(self, peer, prefix='', bus='', subscribed=True, reverse=False):
        return self.rpc().call(peer, 'pubsub.list', prefix,
                               bus, subscribed, reverse)

    def add_subscription(self, peer, prefix, callback, bus=''):
        if not callable(callback):
            raise ValueError('callback %r is not callable' % (callback,))
        try:
            buses = self._my_subscriptions[peer]
        except KeyError:
            self._my_subscriptions[peer] = buses = {}
        try:
            subscriptions = buses[bus]
        except KeyError:
            buses[bus] = subscriptions = {}
        try:
            callbacks = subscriptions[prefix]
        except KeyError:
            subscriptions[prefix] = callbacks = set()
        callbacks.add(callback)

    def add_ext_subscription(self, prefix, callback):
        if not callable(callback):
            raise ValueError('callback %r is not callable' % (callback,))
        try:
            callbacks = self._my_ext_subscriptions[prefix]
        except KeyError:
            self._my_ext_subscriptions[prefix] = callbacks = set()
        callbacks.add(callback)

    @dualmethod
    @spawn
    def subscribe(self, peer, prefix, callback, bus=''):
        '''Subscribe to topic and register callback.

        Subscribes to topics beginning with prefix. If callback is
        supplied, it should be a function taking four arguments,
        callback(peer, sender, bus, topic, headers, message), where peer
        is the ZMQ identity of the bus owner sender is identity of the
        publishing peer, topic is the full message topic, headers is a
        case-insensitive dictionary (mapping) of message headers, and
        message is a possibly empty list of message parts.
        '''

        self.add_subscription(peer, prefix, callback, bus)

        _log.debug('PUBSUB Inside REQUIRED subscribe')
        #Subscribe to external
        self.pubsub_external.subscribe(prefix, callback)
        #Subscribe to local
        return self.rpc().call(peer, 'pubsub.subscribe', prefix, bus=bus)

        # if self.pubsub_external.is_external(prefix):
        #     self.add_ext_subscription(prefix, callback)
        #     try:
        #         callbacks = self._my_ext_subscriptions[prefix]
        #     except KeyError:
        #         self._my_ext_subscriptions[prefix] = callbacks = set()
        #     callbacks.add(callback)
        #     return self.pubsub_external.subscribe(prefix, callback)
        # else:
        #     return self.rpc().call(peer, 'pubsub.subscribe', prefix, bus=bus)

    @subscribe.classmethod
    def subscribe(cls, peer, prefix, bus=''):
        _log.debug('PUBSUB Inside other subscribe')
        def decorate(method):
            annotate(method, set, 'pubsub.subscriptions', (peer, bus, prefix))
            return method
        return decorate

    def drop_subscription(self, peer, prefix, callback, bus=''):
        buses = self._my_subscriptions[peer]
        if prefix is None:
            if callback is None:
                subscriptions = buses.pop(bus)
                topics = subscriptions.keys()
            else:
                subscriptions = buses[bus]
                topics = []
                remove = []
                for topic, callbacks in subscriptions.iteritems():
                    try:
                        callbacks.remove(callback)
                    except KeyError:
                        pass
                    else:
                        topics.append(topic)
                    if not callbacks:
                        remove.append(topic)
                for topic in remove:
                    del subscriptions[topic]
                if not subscriptions:
                    del buses[bus]
            if not topics:
                raise KeyError('no such subscription')
        else:
            subscriptions = buses[bus]
            if callback is None:
                del subscriptions[prefix]
            else:
                callbacks = subscriptions[prefix]
                callbacks.remove(callback)
                if not callbacks:
                    del subscriptions[prefix]
            topics = [prefix]
            if not subscriptions:
                del buses[bus]
        if not buses:
            del self._my_subscriptions[peer]
        return topics

    def unsubscribe(self, peer, prefix, callback, bus=''):
        '''Unsubscribe and remove callback(s).

        Remove all handlers matching the given handler ID, which is the
        ID returned by the subscribe method. If all handlers for a
        topic prefix are removed, the topic is also unsubscribed.
        '''
        topics = self.drop_subscription(peer, prefix, callback, bus)
        return self.rpc().call(peer, 'pubsub.unsubscribe', topics, bus=bus)

    def publish(self, peer, topic, headers=None, message=None, bus=''):
        '''Publish a message to a given topic via a peer.

        Publish headers and message to all subscribers of topic on bus
        at peer. If peer is None, use self. Adds volttron platform version
        compatibility information to header as variables
        min_compatible_version and max_compatible version
        '''
        #_log.debug("In pusub.publsih. headers in pubsub publish {}".format(
        #    headers))
        #_log.debug("In pusub.publsih. topic {}".format(topic))
        #_log.debug("In pusub.publsih. Message {}".format(message))
        if headers is None:
            headers = {}
        headers['min_compatible_version'] = min_compatible_version
        headers['max_compatible_version'] = max_compatible_version

        if peer is None:
            peer = 'pubsub'

        if self.pubsub_external.is_external(topic):
            return self.pubsub_external.publish(topic, headers, message)
        else:
            return self.rpc().call(
                peer, 'pubsub.publish', topic=topic, headers=headers,
                message=message, bus=bus)

    def _check_if_protected_topic(self, topic):
        required_caps = self.protected_topics.get(topic)
        if required_caps:
            user = str(self.rpc().context.vip_message.user)
            caps = self.rpc().call('auth', 'get_capabilities',
                                   user_id=user).get(timeout=5)
            if not set(required_caps) <= set(caps):
                msg = ('to publish to topic "{}" requires capabilities {},'
                      ' but capability list {} was'
                      ' provided').format(topic, required_caps, caps)
                raise jsonrpc.exception_from_json(jsonrpc.UNAUTHORIZED, msg)

    def _peer_get_external_message(self, topic, headers, message):
        #_log.debug("PUBSUB Got sub message : {}".format(message))
        _log.debug("PUBSUB Got ext sub message {}".format(topic))
        try:
            for prefix, callbacks in self._my_ext_subscriptions.iteritems():
                #_log.debug("PUBSUB Got sub message ss {}".format(callback))
                if topic.startswith(prefix):
                    for callback in callbacks:
                        callback(self.core().identity, 'pubsub', '', topic, headers, message)
        except KeyError:
            _log.debug("PUBSUB key error")
            pass


class ProtectedPubSubTopics(object):
    '''Simple class to contain protected pubsub topics'''
    def __init__(self):
        self._dict = {}
        self._re_list = []

    def add(self, topic, capabilities):
        if isinstance(capabilities, basestring):
            capabilities = [capabilities]
        if len(topic) > 1 and topic[0] == topic[-1] == '/':
            regex = re.compile('^' + topic[1:-1] + '$')
            self._re_list.append((regex, capabilities))
        else:
            self._dict[topic] = capabilities

    def get(self, topic):
        if topic in self._dict:
            return self._dict[topic]
        for regex, capabilities in self._re_list:
            if regex.match(topic):
                return capabilities
        return None


class PubSubExt(object):
    def __init__(self, owner):

        self._local_hub = (os.environ.get('VOLTTRON_PUB_ADDR'),
                           os.environ.get('VOLTTRON_SUB_ADDR'))
        print("local hub #1 (PUB, SUB): {}".format(self._local_hub))
        if not (self._local_hub[0] and self._local_hub[1]):
            raise ValueError('VOLTTRON_PUB_ADDR and VOLTTRON_SUB_ADDR must '
                             'be set.')

        _log.debug("local hub (PUB, SUB): {}".format(self._local_hub))
        # self._hub_hash = md5.md5()
        self._subscriptions = {}
        self._context = zmq.Context.instance()
        self._owner = owner
        self._sockets = {}
        self._greenlets = {}
        self._event_queue = Queue()
        self._retry_period = 300.0

        # This is where we publish to.  It will use self._local_hub for
        # the connection to it.
        self._source_socket = self._get_socket(self._local_hub[1], zmq.PUB)
        # Local hub to subscribe to messages from other platforms.
        self._sink_socket = self._get_socket(self._local_hub[0], zmq.SUB)

        #self._get_socket(self._local_hub[0], zmq.SUB)

    def _get_socket(self, addr, type):
        key = (addr, type)
        socket = self._sockets.get(key)
        if not socket:
            socket = self._context.socket(type)
            socket.connect(addr)
            self._sockets[key] = socket

        if not socket:
            _log.error("Invalid socket detected for {}".format(key))
        return socket

    def subscribe(self, prefix, callback):
        """Subscribe to topic and register callback.

        Subscribes to topics beginning with prefix. If callback is
        supplied, it should be a function taking four arguments,
        callback(peer, sender, bus, topic, headers, message), where peer
        is the ZMQ identity of the bus owner sender is identity of the
        publishing peer, topic is the full message topic, headers is a
        case-insensitive dictionary (mapping) of message headers, and
        message is a possibly empty list of message parts.
        """
        _log.debug("SUB: Subscribing to prefix {}".format(prefix))
        if not self._sink_socket:
            raise SubsriptionError('Invalid subscriber address')

        _log.debug("SUB: Subscription keys: {}".format(self._subscriptions.keys()))
        # if we have a subscription entry, let's remove and resubscribe
        #to do

        self._subscriptions[prefix] = {
            'subscribed_at': get_aware_utc_now(),
            'address': self._local_hub[0],
            'callbacks': []
        }

        # Subscribe to local hub
        self._set_prefix_callback(self._sink_socket, prefix, callback)
        _log.debug("SUB: local hub subscription")
        if self._sink_socket not in self._greenlets.keys():
            _log.debug("SUB: Spawning greenlet for local hub subscription")
            self._greenlets[self._sink_socket] = {
                'greenlets': [],
                'address': self._local_hub[0],
            }
            greenlet = gevent.spawn(self._make_subscription, self._sink_socket)
            self._greenlets[self._sink_socket]['greenlets'].append(greenlet)
            processgreenlet = gevent.spawn(self._process_loop)
            self._greenlets[self._sink_socket]['greenlets'].append(processgreenlet)
        else:
            _log.debug("SUB: Greenlet already exists for local hub subscription")

        # Subscribe to external hubs
        _log.debug("External hub subscription")
        addresskeys = self._owner.rpc().call('pubsubhub', 'get_hubs').get(timeout=2)
        for pub, sub in addresskeys:
            if pub != self._local_hub[0]:
                _log.debug("External pub sub {} {}".format(pub, sub))
                socket = self._get_socket(pub, zmq.SUB)

                if socket:
                    _log.debug("Creating subscription for prefix '{}'"
                               .format(prefix))
                    self._set_prefix_callback(socket, prefix, callback)
                    if socket not in self._greenlets.keys():
                        _log.debug("SUB: Spawning greenlet for local hub subscription")
                        self._greenlets[socket] = {
                            'greenlets': [],
                            'address': pub
                        }
                        greenlet = gevent.spawn(self._make_subscription, socket)
                        self._greenlets[socket]['greenlets'].append(greenlet)
                        processgreenlet = gevent.spawn(self._process_loop)
                        self._greenlets[socket]['greenlets'].append(processgreenlet)
                    else:
                        _log.debug("SUB: Greenlet already exists for local hub subscription")

    def publish(self, topic, headers=None, message=None):
        '''Publish a message to a given topic via a peer.

        Publish headers and message to all subscribers of topic on bus
        at peer. If peer is None, use self. Adds volttron platform version
        compatibility information to header as variables
        min_compatible_version and max_compatible version
        '''
        #print('PUBLISHING TOPIC: {}'.format(topic))
        if headers is None:
            headers = {}
        headers['min_compatible_version'] = min_compatible_version
        headers['max_compatible_version'] = max_compatible_version
        headers['sent_from'] = self._local_hub[0]

        json_msg = jsonapi.dumps(
            dict(headers=headers, message=message)
        )
        #topic should not be part of json msg
        data = "%s %s"%(topic, json_msg)

        frames = [zmq.Frame(str(data))]
        greenlet = gevent.spawn(self._source_socket.send_multipart(frames, copy=False))
        gevent.sleep(0.1)
        return greenlet

    def _set_prefix_callback(self, socket, prefix, callback):
        if prefix == '':
            _log.info('_make_subscription: subscribing to entire message bus')
        else:
            _log.info('_make_subscription: subscribing to prefix {}'.format(prefix))

        socket.setsockopt(zmq.SUBSCRIBE, str(prefix))
        self._subscriptions[prefix]['callbacks'].append(callback)

    #Subscribe loop for external hub subscriptions
    def _make_subscription(self, socket):

        while True:
            data = socket.recv()
            #_log.debug("PUBSUB Got ext sub message : ")
            self._event_queue.put(data)

    #Incoming message processing loop
    def _process_loop(self):
        new_msg_list = []
        #_log.debug("Reading from/waiting for queue.")
        while True:
            try:
                new_msg_list = []
                #_log.debug("PUBSUB Reading from/waiting for queue.")
                new_msg_list = [
                     self._event_queue.get(True, self._retry_period)]

            except Empty:
                #_log.debug("Queue wait timed out. Falling out.")
                new_to_publish = []

            if len(new_msg_list) != 0:
                #_log.debug("Checking for queue build up.")
                while True:
                    try:
                        new_msg_list.append(self._event_queue.get_nowait())
                    except Empty:
                        break

            #_log.debug('SUB: Length of data got from event queue {}'.format(len(new_msg_list)))
            for data in new_msg_list:
                json0 = data.find('{')
                topic = data[0:json0 - 1]
                d = jsonapi.loads(data[json0:])
                # _log.debug("PUBSUB Got ext sub message : {}".format(d['message']))

                for prefix in self._subscriptions.keys():
                    if self.is_subscription(topic, prefix):
                        #_log.debug('SUB: subscription already present...calling all callbacks')

                        for callback in self._subscriptions[prefix]['callbacks']:
                            callback(self._owner.core().identity, 'pubsub', '', topic,
                                     d['headers'], d['message'])
                    else:
                        _log.debug('SUB: subscription not matching {}'.format(topic))

    def is_external(self, prefix):
        return prefix[:len('devices')] == 'devices' or prefix == ''

    def is_subscription(self, topic, prefix):
        return topic[:len(prefix)] == prefix or prefix == ''

