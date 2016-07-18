from multiprocessing import Process, Lock, JoinableQueue
from gevent.queue import Queue, Empty
import sys
import gevent
import logging
from datetime import timedelta
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent
from volttron.platform.agent.utils import setup_logging
import os


setup_logging()
_log = logging.getLogger('multiagent')

class MultiAgent(Process):
    def __init__(self, lock, msgque):
        Process.__init__(self)
        self.lock = lock
        self.msgque = msgque
        agent = Agent()
        event = gevent.event.Event()
        self.task = gevent.spawn(agent.core.run, event)
        event.wait(timeout=2)
        agent.vip.pubsub.subscribe('pubsub',
                                   'devices',
                                   self.on_message)
        _log.debug("Process id: {}".format(os.getpid()
                                           ))
        self.count = 0
        self.delta_list = []
        self.msg = []

    def on_message(self, peer, sender, bus, topic, headers, message):
        '''Use match_all to receive all messages and print them out.'''
        client_time = utils.get_aware_utc_now()
        utcnow_string = utils.format_timestamp(client_time)
        self.count += 1
        _log.debug(
            "Process name: %r, Count: %r, Time: %r, Peer: %r, Sender: %r:, Bus: %r, Topic: %r, Headers: %r, "
            "Message: %r ", self.name, self.count, utcnow_string, peer, sender, bus, topic, headers, message)
        header_time = utils.parse_timestamp_string(headers['TimeStamp'])

        if self.count%42 == 0:
            diff = client_time - header_time
            self.msg.append(diff)
        #self.delta_list.append(diff)
        #avg = sum(self.delta_list, timedelta(0))/len(self.delta_list)

        if(self.count == 420):
            self.queue_put(self.msg)

    def queue_put(self, msg):
        self.lock.acquire()
        self.msgque.put(msg)
        self.lock.release()

def main(argv=sys.argv):
    try:
        proc = []
        msg = []
        l = Lock()
        msgQ = JoinableQueue()
        proc = [MultiAgent(l, msgQ) for i in range(100)]
        for p in proc:
            _log.debug("Process name {0}, Process Id: {1}".format(p.name, p.pid))
            p.start()

        #Wait for queue to be done
        while True:
            if not msgQ.empty():
                msg.append(msgQ.get(True))
                msgQ.task_done()
                _log.debug("msg len {0}, proc len {1}".format(len(msg), len(proc)))
                if len(msg) == len(proc):
                    break
            gevent.sleep(1)
        #Display the stats
        avg = []
        t = []

        _log.debug("len : {0} {1} ".format(len(msg), len(msg[0])))
        print("Mean time {}".format(avg))
        #Plot it into a graph later
        avg = []
        t = []
        for i in range(10):
            t = []
            for j in range(len(msg)):
                t.append(msg[j][i])
            avg.append(sum(t, timedelta(0))/len(t))
        print("Mean time {}".format(avg))

        for p in proc:
            p.task.join()
    except KeyboardInterrupt:
        for p in proc:
            p.task.kill()
        _log.debug("KEYBOARD INTERRUPT")

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())