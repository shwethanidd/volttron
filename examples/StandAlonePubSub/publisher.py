import sys

import gevent

import pubsubconfig
from volttron.platform.vip.agent import Agent, Core


class PublisherAgent(Agent):

    def __init__(self, topic, **kwargs): 
        super(PublisherAgent, self).__init__(**kwargs)
        self._topic = topic

    @Core.receiver('onstart')
    def start(self, sender, **kwargs):
        self.pub('This is a test message\n')

    def pub(self, message):
        sys.stdout.write('publishing to topic: {}\n'.format(self._topic))
        self.vip.pubsub.publish('pubsub', self._topic, message=message)

if  __name__ == '__main__':
    try:
        args = pubsubconfig.setup()

        agent = PublisherAgent(args.topic, address=args.vip_address,
            publickey=args.publickey, secretkey=args.secretkey, 
            serverkey=args.server_key)

        task = gevent.spawn(agent.core.run)

        try:
            task.join()
        finally:
            task.kill()
    except KeyboardInterrupt:
        pass
