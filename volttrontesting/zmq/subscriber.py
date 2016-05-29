import sys
import zmq.green as zmq

port = "5000"
# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
print "Collecting updates from server..."
addr = "tcp://127.0.0.1:%s" % port
print(addr)
socket.connect(addr)
topicfilter = ""
socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
for update_nbr in range(10):
    string = socket.recv()
    topic, messagedata = string.split()
    print topic, messagedata