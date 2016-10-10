# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2016, Battelle Memorial Institute
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
import random
import re
import weakref

from zmq import green as zmq
from zmq import SNDMORE
from zmq.utils import jsonapi

from .base import SubsystemBase
from ..decorators import annotate, annotations, dualmethod, spawn
from ..errors import Unreachable
from .... import jsonrpc
from volttron.platform.agent import utils
import gevent
from gevent.queue import Queue, Empty
from .pubsubcpp import PubSubCy
import threading
import time

__all__ = ['PubSub', 'PubSubCy']
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


class PubSub(SubsystemBase):
    def __init__(self, core, rpc_subsys, peerlist_subsys, owner):
        self.core = weakref.ref(core)
        self.rpc = weakref.ref(rpc_subsys)
        self.peerlist = weakref.ref(peerlist_subsys)
        self._peer_subscriptions = {}
        self._my_agent_subscriptions = {}
        self.protected_topics = ProtectedPubSubTopics()
        self._event_queue = Queue()
        self._retry_period = 300.0
        self._cypubsub = PubSubCy(self.core().socket)
        #self._processgreenlet = gevent.spawn(self._process_loop)
        self._cython = True

        def setup(sender, **kwargs):
            # pylint: disable=unused-argument
            rpc_subsys.export(self._peer_sync, 'pubsub.sync')
            rpc_subsys.export(self._peer_subscribe, 'pubsub.subscribe')
            rpc_subsys.export(self._peer_unsubscribe, 'pubsub.unsubscribe')
            rpc_subsys.export(self._peer_list, 'pubsub.list')
            rpc_subsys.export(self._peer_publish, 'pubsub.publish')
            rpc_subsys.export(self._peer_push, 'pubsub.push')
            core.onconnected.connect(self._connected)
            core.onviperror.connect(self._viperror)
            peerlist_subsys.onadd.connect(self._peer_add)
            peerlist_subsys.ondrop.connect(self._peer_drop)

            def subscribe(member):   # pylint: disable=redefined-outer-name
                for peer, bus, prefix in annotations(
                        member, set, 'pubsub.subscriptions'):
                    # XXX: needs updated in light of onconnected signal
                    if self._cython: self._cypubsub.add_my_subscriptions(peer, prefix, member, bus)
            inspect.getmembers(owner, subscribe)
        core.onsetup.connect(setup, self)

    def add_bus(self, name):
        self._cypubsub.add_bus(name)

    def remove_bus(self, name):
        self._cypubsub.remove_bus(name)
        # XXX: notify subscribers of removed bus
        #      or disallow removal of non-empty bus?

    def _connected(self, sender, **kwargs):
        self.synchronize(None)

    def _viperror(self, sender, error, **kwargs):
        if isinstance(error, Unreachable):
            self._peer_drop(self, error.peer)

    def _peer_add(self, sender, peer, **kwargs):
        # Delay sync by some random amount to prevent reply storm.
        #_log.debug("peer add {}".format(peer))
        delay = random.random()
        self.core().spawn_later(delay, self.synchronize, peer)

    def _peer_drop(self, sender, peer, **kwargs):
        #_log.debug("peer drop {}".format(peer))
        self._sync(peer, {})

    #Inside subscriber
    def _sync(self, peer, items):
        #_log.debug("Inside pubsub _sync: {}".format(peer))
        self._cypubsub.sync(peer, items)

    def _peer_sync(self, items):
        #_log.debug("Inside pubsub _peer_sync: {}".format(items))
        peer = bytes(self.rpc().context.vip_message.peer)
        assert isinstance(items, dict)
        self._sync(peer, items)

    def _peer_subscribe(self, prefix, bus=''):
        peer = bytes(self.rpc().context.vip_message.peer)
        for prefix in prefix if isinstance(prefix, list) else [prefix]:
            self._cypubsub.add_peer_subscriptions(peer, prefix, bus)

    def _peer_unsubscribe(self, prefix, bus=''):
        _log.debug("_peer_unsubscribe: {0}, {1} ".format(prefix, bus))
        peer = bytes(self.rpc().context.vip_message.peer)
        self._cypubsub.peer_unsubscribe(peer, prefix, bus)
        _log.debug("Reached here after cy peer unsubscribe")

    def _peer_list(self, prefix='', bus='', subscribed=True, reverse=False):
        peer = bytes(self.rpc().context.vip_message.peer)
        return self._cypubsub.peer_list(peer, prefix, bus, subscribed, reverse)

    def _peer_publish(self, topic, headers, message=None, bus=''):
        peer = bytes(self.rpc().context.vip_message.peer)
        self._cypubsub.set_socket(self.core().socket)
        self._cypubsub.distribute(peer, topic, headers, message, bus)
        #greenlet = gevent.spawn(self._cypubsub.distribute(peer, topic, headers, message, bus))
        #tm = utils.get_aware_utc_now()
        # Start router in separate thread to remain responsive
        # thread = threading.Thread(target=self.distr, args=(peer, topic, headers, message, bus))
        # thread.daemon = True
        # thread.start()
        # thread.join(1)

    def _peer_push(self, sender, bus, topic, headers, message):
        peer = bytes(self.rpc().context.vip_message.peer)
        self._cypubsub.peer_push(peer, sender, headers, topic, message, bus)

    def add_subscription(self, peer, prefix, callback, bus=''):
        if not callable(callback):
            raise ValueError('callback %r is not callable' % (callback,))
        try:
            buses = self._my_agent_subscriptions[peer]
        except KeyError:
            self._my_agent_subscriptions[peer] = buses = {}
        try:
            subscriptions = buses[bus]
        except KeyError:
            buses[bus] = subscriptions = {}
        try:
            callbacks = subscriptions[prefix]
        except KeyError:
            subscriptions[prefix] = callbacks = set()
        callbacks.add(callback)

    def synchronize(self, peer):
        if peer is None:
            peer = ''
        items = {}
        items = self._cypubsub.synchronize(peer)
        for peer in items.keys():
            subscriptions = items[peer]
            self.rpc().notify(peer, 'pubsub.sync', subscriptions)#To do

    def list(self, peer, prefix='', bus='', subscribed=True, reverse=False):
        return self.rpc().call(peer, 'pubsub.list', prefix,
                                bus, subscribed, reverse)

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
        _log.debug("subscribe {0}, {1}, {2}".format(peer, prefix, bus))
        self.add_subscription(peer, prefix, callback, bus)
        self._cypubsub.add_my_subscriptions(peer, prefix, callback, bus)
        return self.rpc().call(peer, 'pubsub.subscribe', prefix, bus=bus)
    
    @subscribe.classmethod
    def subscribe(cls, peer, prefix, bus=''):
        def decorate(method):
            _log.debug("subscribe decorator {0}, {1}, {2}".format(peer, prefix, bus))
            annotate(method, set, 'pubsub.subscriptions', (peer, bus, prefix))
            return method
        return decorate

    def drop_subscription(self, peer, prefix, callback, bus=''):
        return self._cypubsub.drop_subscription(peer, prefix, callback, bus)

    def unsubscribe(self, peer, prefix, callback, bus=''):
        topics = self.drop_subscription(peer, prefix, callback, bus)
        _log.debug("unsubscribe after drop: {0}, {1} ".format(prefix, topics))
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
        return self.rpc().call(
            peer, 'pubsub.publish', topic=topic, headers=headers,
            message=message, bus=bus)

    def print_my_sub(self):
        _log.debug("Calling print my sub")
        self._cypubsub.print_my_subscriptions('pubsub')

    def _msg_queue_add(self, data):
        self._event_queue.put(data)

    # Incoming message processing loop
    def _process_loop(self):
        while True:
            try:
                new_msg_list = [
                    self._event_queue.get(True, self._retry_period)]

            except Empty:
                new_msg_list = []

            if new_msg_list:
                while True:
                    try:
                        new_msg_list.append(self._event_queue.get_nowait())
                    except Empty:
                        break

            for data in new_msg_list:
                peer = data['peer']
                bus = data['bus']
                topic = data['topic']
                sender = data['sender']
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
                                callback(peer, sender, bus, topic, data['headers'], data['message'])
                if not handled:
                    # No callbacks for topic; synchronize with sender
                    self.synchronize(peer)

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

    # Main loops
    def distr(self, peer, topic, headers, message, bus):
        try:
            self._cypubsub.distribute(peer, topic, headers, message, bus)
        except Exception:
            _log.exception('Unhandled exception in Distribute')
            raise

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



