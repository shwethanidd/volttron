from apiutils import *
import base64
import time
import json

api = APITester("http://127.0.0.1:8080/jsonrpc")
identity_list = ['platform.actuator', 'AlerterAgent', 'listeneragent-3.2_1', 'OverrideAgent', 'thresholdagent', 'AgentWatcher']

platforms = api.do_rpc("list_platforms")

# Specific platform not the same as vcp on the platform
platform_uuid = platforms[0]['uuid']

print("Platform", platform_uuid)

agents = api.list_agents(platform_uuid)

# print agents

for agent in agents:
    #print(agent)
    if agent['identity'] in identity_list:
        if not agent['is_running']:
            print("Starting agent {}".format(agent['identity']))
            result = api.start_agent(platform_uuid, [agent['uuid']])
            print (result)

time.sleep(10)
new_config = {
    "devices/fake-campus/fake-building/fake-device/all": {
        "temperature": {
            "threshold_max": 70,
            "threshold_min": 40
        },
        "PowerState": {
            "threshold_max": 42
        }
    }
}

threshold_identity = 'thresholdagent'
response = api.store_agent_config(platform_uuid, threshold_identity, 'config', json.dumps(new_config), 'json')
assert response is None
response = api.get_agent_config(platform_uuid, threshold_identity, 'config')
response = json.loads(response)
assert new_config["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_max"] == \
       response["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_max"]
assert new_config["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_min"] == \
       response["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_min"]

time.sleep(30)

new_config["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_max"] = 90
new_config["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_min"] = 40
response = api.store_agent_config(platform_uuid, threshold_identity, 'config', json.dumps(new_config), 'json')
assert response is None
response = api.get_agent_config(platform_uuid, threshold_identity, 'config')
response = json.loads(response)
assert new_config["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_max"] == \
       response["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_max"]
assert new_config["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_min"] == \
       response["devices/fake-campus/fake-building/fake-device/all"]["temperature"]["threshold_min"]

time.sleep(120)
agents = api.list_agents(platform_uuid)

for agent in agents:
    print(agent)
    if agent['identity'] in identity_list:
        if agent['is_running']:
            print("Stopping agent {}".format(agent['identity']))
            result = api.stop_agent(platform_uuid, [agent['uuid']])
            print (result)

# for agent in agents:
#     print (agent)
#     if agent['identity'].startswith('actuatoragent-1.0'):
#         result = api.stop_agent(platform_uuid, [agent['uuid']])
#         print (result)
#         result = api.remove_agent(platform_uuid, [agent['uuid']])
#         print (result)
#
# with open('/home/jer/.volttron/packaged/listeneragent-3.0-py2-none-any.whl') as f:
#     encoded = base64.b64encode(f.read())
#
#
#     files =  [
#                 {
#                     "file_name": "listeneragent-3.0-py2-none-any.whl",
#                     "file": "data:application/octet-stream;base64,{}".format(encoded)
#                 }
#             ]
#
#
#     agents = api.install_agent(platform_uuid, files)
#
#     print(agents)
#     print ("thing", agents.json())
#
#     for agent in agents.json()['result']:
#         print(agent)
#         result = api.start_agent(platform_uuid, [agent['uuid']])
#         print (result)


