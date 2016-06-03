import sys
import zmq.green as zmq

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
print "Collecting updates from server..."
#addr = "ipc://@/home/vdev/.volttron/run/publish"
addr = "tcp://127.0.0.2:5000"
print(addr)
socket.connect(addr)
topicfilter = ""
socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
while True:
    string = socket.recv()
    print string
