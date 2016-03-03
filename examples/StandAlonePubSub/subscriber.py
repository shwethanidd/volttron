import sys

import json
import logging
import gevent

import pubsubconfig
from volttron.platform.vip.agent import Agent, Core
from volttron.platform.agent import utils

_log = logging.getLogger(__name__)


class SubscriberAgent(Agent):
    ''' A standalone agent that subscribes to one topic'''

    def __init__(self, topic, **kwargs): 
        super(SubscriberAgent, self).__init__(**kwargs)
        self._topic = topic

    def onmessage(self, peer, sender, bus, topic, headers, message):
        '''Handle incoming messages on the bus.'''
        sys.stdout.write(message)
        sys.stdout.flush()

    @Core.receiver('onstart')
    def start(self, sender, **kwargs):
        '''Handle the starting of the agent.'''
        sys.stdout.write('subscribing to topic: {}\n'.format(self._topic))
        self.vip.pubsub.subscribe(peer='pubsub', 
                   prefix=self._topic,
                   callback=self.onmessage).get(timeout=5)

      
if  __name__ == '__main__':
    try:
        args = pubsubconfig.setup()

        agent = SubscriberAgent(args.topic, address=args.vip_address,
            publickey=args.publickey, secretkey=args.secretkey, 
            serverkey=args.server_key)

        task = gevent.spawn(agent.core.run)

        try:
            task.join()
        finally:
            task.kill()
    except KeyboardInterrupt:
        pass
