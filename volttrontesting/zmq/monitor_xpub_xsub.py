# -*- coding: utf-8 -*-
# Inspired from
# https://raw.githubusercontent.com/zeromq/pyzmq/master/examples/monitoring/simple_monitor.py
"""Simple example demonstrating the use of the socket monitoring feature."""

# This file is part of pyzmq.
#
# Distributed under the terms of the New BSD License. The full
# license is in the file COPYING.BSD, distributed as part of this
# software.
from __future__ import print_function

__author__ = ('Guido Goldstein', 'Craig Allwardt')

import random
import threading
import time

import zmq
from zmq.utils.monitor import recv_monitor_message


line = lambda: print('-' * 40)


print("libzmq-%s" % zmq.zmq_version())
if zmq.zmq_version_info() < (4, 0):
    raise RuntimeError("monitoring in libzmq version < 4.0 is not supported")

EVENT_MAP = {}
print("Event names:")
for name in dir(zmq):
    if name.startswith('EVENT_'):
        value = getattr(zmq, name)
        print("%21s : %4i" % (name, value))
        EVENT_MAP[value] = name


def do_publishing(pub_socket):
    print('Starting publisher')
    publisher_id = random.randrange(10000, 20000)
    while True:
        topic = random.randrange(1, 10)
        messagedata = "server#%s" % publisher_id
        print
        "%s %s" % (topic, messagedata)
        pub_socket.send("%d %s" % (topic, messagedata))
        time.sleep(1)


def do_subscribe(sub_socket):
    print('Starting subscriber')
    topicfilter = ""
    sub_socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
    for update_nbr in range(10):
        string = sub_socket.recv()
        topic, messagedata = string.split()
        print(topic, messagedata)


def do_monitor(capture):
    while True:
        print("DATA CAPTURED: {}".format(capture.recv()))


def do_proxy(frontend, backend, capture):
    try:
        zmq.proxy(frontend, backend, capture)
    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        frontend.close()
        backend.close()


def event_monitor(monitor):
    while monitor.poll():
        evt = recv_monitor_message(monitor)
        evt.update({'description': EVENT_MAP[evt['event']]})
        print("Event: {}".format(evt))
        if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
            break
    monitor.close()
    print()
    print("event monitor thread done!")


ctx = zmq.Context.instance()

subsocketuri = "ipc://@/tmp/subscribe"
pubsocketuri = "ipc://@/tmp/publish"
capturesocketuri = "ipc://@/tmp/capture"

backend = ctx.socket(zmq.PUB)
backend.bind(pubsocketuri)
backendthread = threading.Thread(target=do_publishing, args=(backend,))
backendthread.daemon = True
backendthread.start()

frontend = ctx.socket(zmq.SUB)
frontend.bind(subsocketuri)
frontendthread = threading.Thread(target=do_subscribe, args=(frontend,))
frontendthread.daemon = True
frontendthread.start()

capture = ctx.socket(zmq.PUB)
capture.bind(capturesocketuri)
capturethread = threading.Thread(target=do_monitor, args=(capture,))
capturethread.daemon = True
capturethread.start()

do_proxy(frontend, backend, capture)

#rep = ctx.socket(zmq.REP)
#req = ctx.socket(zmq.REQ)

# monitor = req.get_monitor_socket()
#
# t = threading.Thread(target=event_monitor, args=(monitor,))
# t.daemon = True
# t.start()
#
# line()
# print("bind req")
# req.bind("tcp://127.0.0.1:6666")
# req.bind("tcp://127.0.0.1:6667")
# time.sleep(1)
#
# line()
# print("connect rep")
# rep.connect("tcp://127.0.0.1:6667")
# time.sleep(0.2)
# rep.connect("tcp://127.0.0.1:6666")
# time.sleep(1)
#
# line()
# print("disconnect rep")
# rep.disconnect("tcp://127.0.0.1:6667")
# time.sleep(1)
# rep.disconnect("tcp://127.0.0.1:6666")
# time.sleep(1)
#
# line()
# print("close rep")
# rep.close()
# time.sleep(1)
#
# line()
# print("disabling event monitor")
# req.disable_monitor()
#
# line()
# print("event monitor thread should now terminate")
#
# # Create a new socket to connect to listener, no more
# # events should be observed.
# rep = ctx.socket(zmq.REP)
#
# line()
# print("connect rep")
# rep.connect("tcp://127.0.0.1:6667")
# time.sleep(0.2)
#
# line()
# print("disconnect rep")
# rep.disconnect("tcp://127.0.0.1:6667")
# time.sleep(0.2)
#
# line()
# print("close rep")
# rep.close()
#
# line()
# print("close req")
# req.close()
#
# print("END")
# ctx.term()