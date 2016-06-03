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
# }}}

from __future__ import absolute_import

import logging
import os

import gevent
from gevent.fileobject import FileObject
from zmq import green as zmq
from zmq.utils import jsonapi

from .. platform.vip.agent import (Agent, Core)
from .agent import utils
from .vip.agent.subsystems.pubsub import ProtectedPubSubTopics

__version__ = '0.0.1'

_log = logging.getLogger(__name__)


class PubSubHubService(Agent):
    def __init__(self, protected_topics_file, backend, frontend, *args,
                 **kwargs):
        super(PubSubHubService, self).__init__(*args, **kwargs)
        self._protected_topics_file = os.path.abspath(protected_topics_file)
        self._backend_address = backend
        self._frontend_address = frontend
        self._sockets = {}
        self.vip.rpc.export(self.add_hub, 'add_hub')
        self.vip.rpc.export(self.get_hubs, 'get_hubs')

    @Core.receiver('onstart')
    def setup_agent(self, sender, **kwargs):
        self._read_protected_topics_file()
        self.core.spawn(utils.watch_file, self._protected_topics_file,
                        self._read_protected_topics_file)
        self.vip.pubsub.add_bus('')
        self._pubhub = gevent.spawn(self._start_pubhub)

    def get_hubs(self):
        """ RPC method to retireve a list of tuples for connected hubs.

        :return:
            list of tuples (pub, sub) addresses that have been connected to.
        """
        return self._sockets.keys()

    def add_hub(self, publish_address, subscribe_address):
        """ RPC method that allows the PubSubHub to have another connection

        :param publish_address:
        :param subscribe_address:
        :return:
        """
        key = (publish_address, subscribe_address)
        if key in self._sockets.keys() and self._sockets[key]:
            _log.debug('Socket already connected to {}'
                       .format(key))
        else:
            _log.debug('Connecting to hub {}.'.format(key))
            context = zmq.Context.instance()
            backend = context.socket(zmq.PUB)
            backend.connect(publish_address)

            frontend = context.socket(zmq.SUB)
            frontend.connect(subscribe_address)

            self._sockets[key] = (backend, frontend)

    # ZMQ device not a volttron forwarder.
    def _start_pubhub(self):
        """ Creates the instance's main hub for binding.

        The mechanism is a zmq forwarder which routes publishers to
        subscribers.  This allows a single point of entry to the VOLTTRON
        instance.
        """

        try:
            context = zmq.Context.instance()
            # Socket facing clients
            frontend = context.socket(zmq.SUB)

            frontend.bind(self._frontend_address)
            frontend.setsockopt(zmq.SUBSCRIBE, "")
            _log.debug("Publishes should connect to: {}"
                       .format(self._frontend_address))
            # Socket facing services
            backend = context.socket(zmq.PUB)
            backend.bind(self._backend_address)
            _log.debug("Subscribers should connect to: {}"
                       .format(self._backend_address))

            zmq.device(zmq.FORWARDER, frontend, backend)

        except Exception, e:
            print e
            print "bringing down zmq device"
        finally:
            pass
            _log.debug('target8')
            frontend.close()
            backend.close()
            context.term()

    def _read_protected_topics_file(self):
        _log.info('loading protected-topics file %s',
                  self._protected_topics_file)
        try:
            utils.create_file_if_missing(self._protected_topics_file)
            with open(self._protected_topics_file) as fil:
                # Use gevent FileObject to avoid blocking the thread
                data = FileObject(fil, close=False).read()
                topics_data = jsonapi.loads(data) if data else {}
        except Exception:
            _log.exception('error loading %s', self._protected_topics_file)
        else:
            write_protect = topics_data.get('write-protect', [])
            topics = ProtectedPubSubTopics()
            try:
                for entry in write_protect:
                    topics.add(entry['topic'], entry['capabilities'])
            except KeyError:
                _log.exception('invalid format for protected topics '
                               'file {}'.format(self._protected_topics_file))
            else:
                self.vip.pubsub.protected_topics = topics
                _log.info('protected-topics file %s loaded',
                          self._protected_topics_file)
