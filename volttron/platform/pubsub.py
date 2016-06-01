from __future__ import absolute_import

from base64 import b64encode, b64decode
import inspect
import logging
import os
import random
import re
import weakref
import threading

import gevent
from gevent.fileobject import FileObject
# import zmq
from zmq import green as zmq
from zmq import SNDMORE
from zmq.utils import jsonapi
from zmq.utils.monitor import recv_monitor_message

from volttron.platform.vip.agent import (Agent, Core)

# from .base import SubsystemBase
# from ..decorators import annotate, annotations, dualmethod, spawn
# from ..errors import Unreachable
# from .... import jsonrpc
from .agent import utils
from .vip.agent.subsystems.pubsub import ProtectedPubSubTopics

_log = logging.getLogger(__name__)


# Device code
#

#
# port = "5559"
# context = zmq.Context()
# socket = context.socket(zmq.PUB)
# socket.connect("tcp://localhost:%s" % port)
# publisher_id = random.randrange(0,9999)
# while True:
#     topic = random.randrange(1,10)
#     messagedata = "server#%s" % publisher_id
#     print "%s %s" % (topic, messagedata)
#     socket.send("%d %s" % (topic, messagedata))
#     time.sleep(0.1)

#
# port = "5560"
# # Socket to talk to server
# context = zmq.Context()
# socket = context.socket(zmq.SUB)
# print "Collecting updates from server..."
# socket.connect ("tcp://localhost:%s" % port)
# topicfilter = "1"
# socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
# for update_nbr in range(10):
#     string = socket.recv()
#     topic, messagedata = string.split()
#     print topic, messagedata


class Monitor(threading.Thread):
    '''Monitor thread to log connections.'''

    def __init__(self, sock):
        super(Monitor, self).__init__()
        self.daemon = True
        self.sock = sock
        EVENT_MAP = {}
        _log.debug("Event names:")
        for name in dir(zmq):
            if name.startswith('EVENT_') and name != 'EVENT_ALL':
                value = getattr(zmq, name)
                _log.debug("%21s : %4i" % (name, value))
                EVENT_MAP[value] = name
                # events = {value: name[6:] for name, value in vars(zmq).iteritems()
                #      if name.startswith('EVENT_') and name != 'EVENT_ALL'}

    # def event_monitor(monitor):
    #    while monitor.poll():
    #        evt = recv_monitor_message(monitor)
    #        evt.update({'description': EVENT_MAP[evt['event']]})
    #        print("Event: {}".format(evt))
    #        if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
    #            break
    #    monitor.close()

    def run(self):
        sock = self.sock
        while True:
            evt = recv_monitor_message(sock)
            evt.update({'description': EVENT_MAP[evt['event']]})
            #    _log.debug("Event: {}".format(evt))
            #   event, endpoint = sock.recv_multipart()
            _log.debug("Event: {}".format(evt))
            # event_id, event_value = struct.unpack('=HI', event)
            # event_name = events[event_id]
            # log.info('%s %s %s', event_name, event_value, endpoint)


class PubSubService(Agent):
    def __init__(self, protected_topics_file, publish_address, subscribe_address, *args, **kwargs):
        super(PubSubService, self).__init__(*args, **kwargs)
        self._protected_topics_file = os.path.abspath(protected_topics_file)
        self._publish_address = publish_address
        self._subscribe_address = subscribe_address

    @Core.receiver('onstart')
    def setup_agent(self, sender, **kwargs):
        self._read_protected_topics_file()
        self.core.spawn(utils.watch_file, self._protected_topics_file,
                        self._read_protected_topics_file)
        self.vip.pubsub.add_bus('')
        self._forwarder_greenlet = gevent.spawn(self._start_forwarder)

    # ZMQ device not a volttron forwarder.
    def _start_forwarder(self):

        try:
            context = zmq.Context.instance()
            # Socket facing clients
            frontend = context.socket(zmq.SUB)

            frontend.bind(self._subscribe_address)
            frontend.setsockopt(zmq.SUBSCRIBE, "")
            _log.debug("Publishes should connect to: {}"
                       .format(self._subscribe_address))
            # Socket facing services
            backend = context.socket(zmq.PUB)
            backend.bind(self._publish_address)
            _log.debug("Subscribers should connect to: {}"
                       .format(self._publish_address))

            Monitor(backend.get_monitor_socket()).start()
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

