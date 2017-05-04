from apiutils import *
import base64
import time
import json

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

api = APITester("http://127.0.0.1:8080/jsonrpc")
# identity_list = ['platform.actuator', 'AlerterAgent', 'listeneragent-3.2_1', 'OverrideAgent', 'thresholdagent', 'AgentWatcher']

platforms = api.do_rpc("list_platforms")

# Specific platform not the same as vcp on the platform
platform_uuid = platforms[0]['uuid']

print("Platform", platform_uuid)

agents = api.list_agents(platform_uuid)

running = False
for agent in agents:
    if agent['identity'] == threshold_identity:
        if agent['is_running']:
            running = True
            break

assert running is True

# Change the threshold agent config
response = api.store_agent_config(platform_uuid, threshold_identity, 'config', json.dumps(new_config), 'json')
assert response is None
# Get the config from config store to verify if update was successful
response = api.get_agent_config(platform_uuid, threshold_identity, 'config')
response = json.loads(response)
topic = "devices/fake-campus/fake-building/fake-device/all"
assert new_config[topic]["temperature"]["threshold_max"] == \
       response[topic]["temperature"]["threshold_max"]
assert new_config[topic]["temperature"]["threshold_min"] == \
       response[topic]["temperature"]["threshold_min"]

time.sleep(30)

# Change the threshold agent config again and observe the override behavior
new_config[topic]["temperature"]["threshold_max"] = 90
new_config[topic]["temperature"]["threshold_min"] = 40
response = api.store_agent_config(platform_uuid, threshold_identity, 'config', json.dumps(new_config), 'json')
assert response is None
response = api.get_agent_config(platform_uuid, threshold_identity, 'config')
response = json.loads(response)
assert new_config[topic]["temperature"]["threshold_max"] == \
       response[topic]["temperature"]["threshold_max"]
assert new_config[topic]["temperature"]["threshold_min"] == \
       response[topic]["temperature"]["threshold_min"]
