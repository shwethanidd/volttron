import gevent
import logging
import os
import requests
import tempfile
from volttron.platform.vip.agent import Agent
from volttron.platform.keystore import KeyStore
from volttron.platform.agent.utils import setup_logging

setup_logging()
_log = logging.getLogger('setup_hub')

volttron_instances = [
    {
        'vhome': "/tmp/v1",
        'vip': "tcp://127.0.0.1:22916",
        'pub': "tcp://127.0.0.1:5000",
        'sub': "tcp://127.0.0.1:5001",
        'web': "http://127.0.0.1:8080"
    },
    {
        'vhome': "/tmp/v2",
        'vip': 'tcp://127.0.0.2:22916',
        'pub': "tcp://127.0.0.2:5000",
        'sub': "tcp://127.0.0.2:5001",
        'web': "http://127.0.0.2:8080"
    },
    {
        'vhome': "/tmp/v3",
        'vip': 'tcp://127.0.0.3:22916',
        'pub': "tcp://127.0.0.3:5000",
        'sub': "tcp://127.0.0.3:5001",
        'web': "http://127.0.0.3:8080"
    }
]

z = zip(range(len(volttron_instances)), volttron_instances)

for i, b in z:
    print(i, b)

agents = []

for a in volttron_instances:
    print('starting agent: {}'.format(a['vip']))
    os.environ['VOLTTRON_HOME'] = a['vhome']
    #os.environ['VOLTTRON_VIP_ADDR'] = a['vip']
    os.environ['VOLTTRON_PUB_ADDR'] = a['pub']
    os.environ['VOLTTRON_SUB_ADDR'] = a['sub']
    print(a['web'])
    response = requests.get("{}/discovery/".format(a['web']))
    print(response.json())
    jdata = response.json()
    # tmp = tempfile.NamedTemporaryFile()
    # ks = KeyStore(tmp.name)
    # ks.generate()
    #     a['vip'], keystore.public(), keystore.secret(),
    #     jdata['serverkey']
    # )
    agent = Agent()
    event = gevent.event.Event()
    gevent.spawn(agent.core.run, event)
    event.wait(timeout=2)
    _log.debug(agent.vip.peerlist().get(timeout=5))
    agents.append(agent)

# for a in volttron_instances:
#     print('starting agent: {}'.format(a['vip']))
#     os.environ['VOLTTRON_HOME'] = a['vhome']
#     #os.environ['VOLTTRON_VIP_ADDR'] = a['vip']
#     os.environ['VOLTTRON_PUB_ADDR'] = a['pub']
#     os.environ['VOLTTRON_SUB_ADDR'] = a['sub']
#     print(a['web'])
#     response = requests.get("{}/discovery/".format(a['web']))
#     print(response.json())
#     jdata = response.json()
#     tmp = tempfile.NamedTemporaryFile()
#     ks = KeyStore(tmp.name)
#     ks.generate()
#     #     a['vip'], keystore.public(), keystore.secret(),
#     #     jdata['serverkey']
#     # )
#     agent = Agent(
#         address=a['vip'], publickey=ks.public(), secretkey=ks.secret())
#     event = gevent.event.Event()
#     gevent.spawn(agent.core.run, event)
#     event.wait(timeout=2)
#     print(agent.vip.hello().get(timeout=2))
#     agents.append(agent)
#
print('adding 0 to 2')
print('sub is {}'.format(volttron_instances[0]['sub']))
agents[2].vip.rpc.call(
    'pubsubhub',
    'add_hub',
    volttron_instances[0]['pub'],
    volttron_instances[0]['sub']).get(timeout=2)
#print('pub {} sub {}'.format(pub, sub))

print('adding 0 to 1')
agents[1].vip.rpc.call(
    'pubsubhub',
    'add_hub',
    volttron_instances[0]['pub'],
    volttron_instances[0]['sub']).get(timeout=2)

print(
    """In this set up anything that is published to 0 should go to both 1 and 2.""")

for a in agents:
    a.core.stop()
