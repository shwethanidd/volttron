import gevent
import logging
from gevent.event import Event
from volttron.platform.vip.agent import Agent
from volttron.platform.agent.utils import setup_logging

setup_logging()
_log = logging.getLogger(__file__)

agent = Agent()
event = Event()
gevent.spawn(agent.core.run, event)
event.wait(timeout=5)
del event

agent2 = Agent()
event = Event()
gevent.spawn(agent2.core.run, event)
event.wait(timeout=5)
del event

def on_match_external(topic, headers, message):
    print('EXTERNAL', topic, headers, message)

def on_match(peer, sender, bus,  topic, headers, message):
    print('ACHOO')
    print(topic, headers, message)

#agent.vip.rpc.export(on_match)
gevent.sleep(2)
print('Should be subscribed to all now.')
agent.vip.pubsub.subscribe('pubsub', '', on_match)
agent.vip.pubsub.subscribe_ex('', on_match_external)

# agent.vip.rpc.call(peer='pubsubhub', method='subscribe',
#                    prefix='foobar', callback='on_match')
#agent2.vip.pubsub.publish('pubsub', 'atopic', message='Foo is bar!')




print('After everything is done.')
while True:
    gevent.sleep(2)
    agent2.vip.pubsub.publish(
        'pubsub', 'external', {'PUBLISH_EXTERNAL': True}, message="fuzzybuckets"
    ).get(timeout=5)

    agent2.vip.pubsub.publish(
        'pubsub', 'internal', message="fuzzybuckets"
    ).get(timeout=5)