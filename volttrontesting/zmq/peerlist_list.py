import gevent
import logging
from gevent.event import Event
from volttron.platform.vip.agent import Agent

agent = Agent()
event = Event()
gevent.spawn(agent.core.run, event)
event.wait(timeout=5)
print(agent.vip.peerlist.list().get())