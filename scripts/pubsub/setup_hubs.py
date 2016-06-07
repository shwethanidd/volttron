import gevent
from volttron.platform.vip.agent import Agent

volttron_instances = [
    {
        'vip': "tcp://127.0.0.1:22916",
        'pub': "tcp://127.0.0.1:5000",
        'sub': "tcp://127.0.0.1:5001"
    },
    {
        'vip': 'tcp://127.0.0.2:22916',
        'pub': "tcp://127.0.0.2:5000",
        'sub': "tcp://127.0.0.2:5001"
    },
    {
        'vip': 'tcp://127.0.0.3:22916',
        'pub': "tcp://127.0.0.3:5000",
        'sub': "tcp://127.0.0.3:5001"
    }
]

z = zip([0, 1, 2], volttron_instances)
print(z)

for i, b in z:
    print(i, b)

agents = []

for a in volttron_instances:
    print('starting agent: {}'.format(a['vip']))
    agent = Agent(address=a['vip'])
    event = gevent.event.Event()
    gevent.spawn(agent.core.run, event)
    event.wait(timeout=2)
    print(agent.vip.hello().get(timeout=2))
    agents.append(agent)

