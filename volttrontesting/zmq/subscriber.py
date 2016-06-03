import sys
import zmq.green as zmq
address = None
while address not in (1, 2):
    address = input('Enter subscription address (1=tcp://127.0.0.1, 2=tcp://127.0.0.2):')

if address == 1:
    address = "tcp://127.0.0.1"
else:
    address = "tcp://127.0.0.2"

port = raw_input('Enter subscription port: ')
# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
print "Collecting updates from server..."
#addr = "ipc://@/home/vdev/.volttron/run/publish"
addr = "%s:%s"%(address, port)
print(addr)
socket.connect(addr)
topicfilter = ""
socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
while True:
    string = socket.recv()
    print string
