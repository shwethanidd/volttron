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

from __future__ import print_function, absolute_import

import argparse
import errno
import logging
from logging import handlers
import logging.config
from urlparse import urlparse

import os
import sys
import threading
import uuid

import gevent
from gevent.fileobject import FileObject
import zmq
from zmq import SNDMORE
from zmq import green
# Create a context common to the green and non-green zmq modules.
green.Context._instance = green.Context.shadow(zmq.Context.instance().underlying)
from zmq.utils import jsonapi

from .agent import utils
from .vip.agent import Agent, Core
from .vip.agent.subsystems.pubsub import ProtectedPubSubTopics
from . import jsonrpc
from .vip.socket import Address

class PubSubService(Agent):
    def __init__(self, protected_topics_file, context, pub_address, secretkey=None, publickey=None, *args, **kwargs):
        super(PubSubService, self).__init__(*args, **kwargs)
        self._protected_topics_file = os.path.abspath(protected_topics_file)
        self._logger = logging.getLogger(__name__)
        # if self._logger.level == logging.NOTSET:
        #     self._logger.setLevel(logging.WARNING)
        #self._pub_address = Address(pub_address)

        self._pub_address = pub_address
        self._context = context or zmq.Context.instance()
        self._secretkey = secretkey
        self._publickey = publickey
        #self.rpc = self.rpc
        self._peer_subscriptions = {}
        #Add encryption to the address

    @Core.receiver('onstart')
    def setup_agent(self, sender, **kwargs):
        self._read_protected_topics_file()
        self.core.spawn(utils.watch_file, self._protected_topics_file,
                        self._read_protected_topics_file)
        self.vip.pubsub.add_bus('')
        self.vip.rpc.export(self._peer_subscribe, 'pubsub.subscribe')
        self.vip.rpc.export(self._peer_unsubscribe, 'pubsub.unsubscribe')
        #Create zmq.ROUTER type socket
        self._pub_sock = zmq.Socket(self._context, zmq.ROUTER)
        #Setup keys for the pub address
        #self._set_keys_to_address()
        self._pub_sock.bind(self._pub_address)
        self.add_bus('')
        #Create thread to route publish messages
        # Start pubsub router in separate thread to remain responsive
        thread = threading.Thread(target=self._pubsub_router)#to check
        thread.daemon = True
        thread.start()

        gevent.sleep(0.1)
        if not thread.isAlive():
            sys.exit()

    def _set_keys_to_address(self):
        self._pub_sock.identity = identity = str(uuid.uuid4())
        if not self._pub_address.identity:
            self._pub_address.identity = identity
        if (self._pub_address.secretkey is None and
                    self._pub_address.server not in ['NULL', 'PLAIN'] and
                self._secretkey):
            self._pub_address.server = 'CURVE'
            self._pub_address.secretkey = self._secretkey
        if not self._pub_address.domain:
            self._pub_address.domain = 'vip'
        self._pub_address.bind(self._pub_sock)
        print("PubSub Address {}".format(self._pub_address))
        self._logger.debug('PubSubService bound to %s' % self._pub_address)

    def _read_protected_topics_file(self):
        self._logger.info('loading protected-topics file %s',
                  self._protected_topics_file)
        try:
            utils.create_file_if_missing(self._protected_topics_file)
            with open(self._protected_topics_file) as fil:
                # Use gevent FileObject to avoid blocking the thread
                data = FileObject(fil, close=False).read()
                topics_data = jsonapi.loads(data) if data else {}
        except Exception:
            self._logger.exception('error loading %s', self._protected_topics_file)
        else:
            write_protect = topics_data.get('write-protect', [])
            topics = ProtectedPubSubTopics()
            try:
                for entry in write_protect:
                    topics.add(entry['topic'], entry['capabilities'])
            except KeyError:
                self._logger.exception('invalid format for protected topics '
                               'file {}'.format(self._protected_topics_file))
            else:
                self.vip.pubsub.protected_topics = topics
                self._logger.info('protected-topics file %s loaded',
                          self._protected_topics_file)

    def _add_peer_subscription(self, peer, bus, prefix):
        try:
            subscriptions = self._peer_subscriptions[bus]
        except KeyError:
            self._peer_subscriptions.setdefault(bus, {})
            subscriptions = self._peer_subscriptions[bus]
        try:
            subscribers = subscriptions[prefix]
        except KeyError:
            subscriptions[prefix] = subscribers = set()
        subscribers.add(peer)
        #self._logger.debug("Added peer in subscription list {0} {1}".format(peer, self._peer_subscriptions))

    def add_bus(self, name):
        self._peer_subscriptions.setdefault(name, {})

    def _peer_subscribe(self, prefix, bus=''):
        peer = bytes(self.vip.rpc.context.vip_message.peer)
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

    def _peer_publish(self, frames):
        #for f in frames:
        #    self._logger.debug("received from pub sock: {}".format(f.bytes))
        #REDIRECTION WORKS!!!
        # sender = frames[0]
        # recipient = frames[1]
        # #frames[0] = recipient
        # frames[0] = zmq.Frame(b'Agent0')
        # self._pub_sock.send_multipart(frames, copy=False)

        if len(frames) > 6:
            data = frames[6].bytes
            json0 = data.find('{')
            topic = data[0:json0 - 1]
            msg = jsonapi.loads(data[json0:])
            headers = msg['headers']
            message = msg['message']
            bus = ''
            #peer = bytes(self.vip.rpc.context.vip_message.peer)
            peer = msg['identity']
            bus = msg['bus']
        #self._pub_sock.send_multipart(frames, copy=False)
        self.router_distribute(frames, peer, topic, headers, message, bus)

    def router_distribute(self, frames, peer, topic, headers, message=None, bus=''):
        #self._check_if_protected_topic(topic)

        subscriptions = self._peer_subscriptions[bus]
        subscribers = set()
        for prefix, subscription in subscriptions.iteritems():
            if subscription and topic.startswith(prefix):
                subscribers |= subscription
        if subscribers:
            #sender = encode_peer(peer)
            # json_msg = jsonapi.dumps(jsonrpc.json_method(
            #     None, 'pubsub.push',
            #     [sender, bus, topic, headers, message], None))
            # frames = [zmq.Frame(b''), zmq.Frame(b''),
            #           zmq.Frame(b'RPC'), zmq.Frame(json_msg)]
            #socket = self.core.socket
            for subscriber in subscribers:
                #frames[1] = zmq.Frame(subscriber)
                frames[0] = zmq.Frame(subscriber)
                #self._pub_sock.send(subscriber, flags=SNDMORE)
                self._pub_sock.send_multipart(frames, copy=False)
        return len(subscribers)

    def _distribute(self, peer, topic, headers, message=None, bus=''):
        #self._check_if_protected_topic(topic)
        subscriptions = self._peer_subscriptions[bus]
        subscribers = set()
        for prefix, subscription in subscriptions.iteritems():
            if subscription and topic.startswith(prefix):
                subscribers |= subscription
        if subscribers:
            #sender = encode_peer(peer)
            sender = peer
            json_msg = jsonapi.dumps(jsonrpc.json_method(
                None, 'pubsub.push',
                [sender, bus, topic, headers, message], None))
            frames = [zmq.Frame(b''), zmq.Frame(b''),
                      zmq.Frame(b'RPC'), zmq.Frame(json_msg)]
            socket = self.core.socket
            for subscriber in subscribers:
                socket.send(subscriber, flags=SNDMORE)
                grnlet = gevent.spawn(socket.send_multipart(frames, copy=False))
        return len(subscribers)

    def _pubsub_router(self):
        try:
            while self.poll():
                self.route()
        except Exception:
            self._logger.exception('Unhandled exception in router loop')
            raise
        finally:
            self.core.stop()

    def poll(self):
        return self._pub_sock.poll

    def route(self):
        socket = self._pub_sock

        # Expecting incoming frames:
        #   [SENDER, RECIPIENT, PROTO, USER_ID, MSG_ID, SUBSYS, ...]
        #Check for peer
        frames = socket.recv_multipart(copy=False)
        if len(frames) < 6:
            # Cannot route if there are insufficient frames, such as
            # might happen with a router probe.
            self._logger('too few frames {}'.format(frames))
            return
        else:
            self._peer_publish(frames)