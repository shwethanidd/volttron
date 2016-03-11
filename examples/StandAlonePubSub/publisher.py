import argparse
import sys

import gevent

from pubsubconfig import PubSubConfig
from volttron.platform.vip.agent import Agent, Core


class PublisherAgent(Agent):

    def __init__(self, topic, infile, **kwargs):
        super(PublisherAgent, self).__init__(**kwargs)
        self._topic = topic
        self._infile = infile

    @Core.receiver('onstart')
    def start(self, sender, **kwargs):
        for line in iter(self._infile.readline, b''):
            self.vip.pubsub.publish('pubsub', self._topic, message=line)

if  __name__ == '__main__':
    try:
        config = PubSubConfig()
        config.arg_parser.add_argument('infile', nargs='?',
                type=argparse.FileType('r'), default=sys.stdin)
        args = config.setup()

        agent = PublisherAgent(args.topic, args.infile,
            address=args.vip_address,
            publickey=args.publickey, secretkey=args.secretkey,
            serverkey=args.server_key)

        task = gevent.spawn(agent.core.run)

        try:
            task.join()
        finally:
            task.kill()
    except KeyboardInterrupt:
        pass
