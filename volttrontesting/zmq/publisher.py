import zmq.green as zmq
import random
import sys
import time

port = "5001"
context = zmq.Context()
socket = context.socket(zmq.PUB)
addr = "ipc://@/home/vdev/.volttron/run/subscribe"
#addr = "tcp://127.0.0.1:%s" % port
print('Addr: %s' % addr)
socket.connect(addr)
publisher_id = random.randrange(10000, 20000)
while True:
    topic = random.randrange(1,10)
    messagedata = "server#%s" % publisher_id
    print "%s %s" % (topic, messagedata)
    socket.send("%d %s" % (topic, messagedata))
    time.sleep(1)
