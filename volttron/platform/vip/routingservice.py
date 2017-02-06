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
import re

import gevent
from gevent.fileobject import FileObject
import zmq
import logging
from zmq import SNDMORE, EHOSTUNREACH, ZMQError, EAGAIN, NOBLOCK
from zmq import green
from collections import defaultdict
from ..keystore import KeyStore
from .socket import decode_key, encode_key, Address
from zmq.utils import jsonapi

_log = logging.getLogger(__name__)

# Optimizing by pre-creating frames
_ROUTE_ERRORS = {
    errnum: (zmq.Frame(str(errnum).encode('ascii')),
             zmq.Frame(os.strerror(errnum).encode('ascii')))
    for errnum in [zmq.EHOSTUNREACH, zmq.EAGAIN]
}

class RoutingService(object):
    def __init__(self, socket, poller, ext_address_file, *args, **kwargs):
        self._routing_table = dict()
        self._poller = poller
        self._external_address_file = ext_address_file
        self._ext_sockets = []
        self._ext_addresses = {}
        self._socket_id_mapping = {}

    def setup(self):
        sock = self._socket_class(self.context, zmq.DEALER)
        # sock.router_mandatory = True
        sock.sndtimeo = 0
        sock.tcp_keepalive = True
        sock.tcp_keepalive_idle = 180
        sock.tcp_keepalive_intvl = 20
        sock.tcp_keepalive_cnt = 6
        keystore = KeyStore()
        publickey = str(keystore.public)
        secretkey = str(keystore.secret)
        _log.debug("Keys: {0}, {1}".format(publickey, secretkey))
        for vip_id in self._ext_addresses:
            addr = self._ext_addresses[vip_id]['address']
            server_key = self._ext_addresses[vip_id]['address']
            sock.identity = vip_id
            sock.zap_domain = 'vip'
            ext_platform_address = addr + '?' + 'serverkey=' + server_key + '&' + 'publickey=' + publickey + '&' + 'secretkey=' + secretkey
            address1 = Address(ext_platform_address)
            _log.debug("External address: {}".format(address1))
            try:
                address1.connect(sock)
                self._socket_id_mapping[vip_id] = sock
                _log.debug("establishing connection to {}".format(address1))
            except zmq.error.ZMQError, ex:
                _log.error("ZMQ error on external connection {}".format(ex))
                break
            self._ext_sockets.append(sock)
            self.router_server_socket = sock
            self._poller.register(sock, zmq.POLLIN)

    def read_platform_address_file(self):
        #Read protected topics file and send to router
        try:
            with open(self._external_address_file) as fil:
                # Use gevent FileObject to avoid blocking the thread
                data = FileObject(fil, close=False).read()
                self._ext_addresses = jsonapi.loads(data) if data else {}
        except Exception:
            _log.exception('error loading %s', self._protected_topics_file)

    def disconnect_external_platform(self, vip_ids):
        for id in vip_ids:
            sock = self._socket_id_mapping[id]
            sock.close()

    def get_connected_platforms(self):
        return list(self._socket_id_mapping.keys())

    def send_external(self, vip_id, frames):
        try:
            sock = self._socket_id_mapping[vip_id]
            self._send(sock, frames)
        except KeyError:
            _log.error("Invalid socket connection")

    def _send(self, sock, frames):
        drop = []
        peer_platform = frames[0]
        # Expecting outgoing frames:
        #   [RECIPIENT, SENDER, PROTO, USER_ID, MSG_ID, SUBSYS, ...]

        try:
            # Try sending the message to its recipient
            sock.send_multipart(frames, flags=NOBLOCK, copy=False)
        except ZMQError as exc:
            try:
                errnum, errmsg = error = _ROUTE_ERRORS[exc.errno]
            except KeyError:
                error = None
            if exc.errno == EHOSTUNREACH:
                _log.debug("Host unreachable {}".format(peer_platform.bytes))
                drop.append(bytes(peer_platform))
            elif exc.errno == EAGAIN:
                _log.debug("EAGAIN error {}".format(peer_platform.bytes))
        return drop

    def handle_subsystem(self, frames, user_id):
        """
         Handler for incoming routing table frames. It checks operation frame and directs it for appropriate action handler.
        :param frames list of frames
        :type frames list
        :param user_id user id of the publishing agent. This is required for protected topics check.
        :type user_id  UTF-8 encoded User-Id property
        :returns: response frame to be sent back to the sender
        :rtype: list

        :Return Values:
        response frame to be sent back to the sender
        """
        response = []
        result = None
        sender, recipient, proto, usr_id, msg_id, subsystem = frames[:6]

        if subsystem.bytes == b'routing_table':
            try:
                op = bytes(frames[6])
            except IndexError:
                return False

            if op == b'add':
                result = self._add_entry(frames)
            elif op == b'remove':
                try:
                    result = self._remove_entry(frames)
                except IndexError:
                    #send response back -- Todo
                    return

        if result is not None:
            #Form response frame
            response = [sender, recipient, proto, user_id, msg_id, subsystem]
            response.append(zmq.Frame(b'request_response'))
            response.append(zmq.Frame(bytes(result)))

        return response


    def _add_entry(self, frames):
        return 0

    def _remove_entry(self, frames):
        return 0