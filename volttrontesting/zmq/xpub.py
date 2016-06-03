import os

import zmq.green as zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator


def main():

    ctx = zmq.Context.instance()

    try:
        print('result1')
        backend = ctx.socket(zmq.PUB)
        backend.bind("tcp://*:5000")
        print('result2')
#       context = zmq.Context(1)
        # Socket facing clients
        frontend = ctx.socket(zmq.SUB)
        print('result3')
        print('result4')
        frontend.bind("tcp://*:5001")

        frontend.setsockopt(zmq.SUBSCRIBE, "")
        print('result5')
        zmq.device(zmq.FORWARDER, frontend, backend)
        print('result6')
    except Exception, e:
        print e
        print "bringing down zmq device"
    finally:
        pass
        frontend.close()
        backend.close()
        ctx.term()

if __name__ == "__main__":
    main()


