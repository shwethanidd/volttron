from apiutils import *
import base64
import time
import json

api = APITester("http://127.0.0.1:8080/jsonrpc")
# identity_list = ['platform.actuator', 'AlerterAgent', 'listeneragent-3.2_1', 'OverrideAgent', 'thresholdagent', 'AgentWatcher']
identity_list = ['listeneragent-3.2_1', 'thresholdagent']

platforms = api.do_rpc("list_platforms")

# Specific platform not the same as vcp on the platform
platform_uuid = platforms[0]['uuid']

print("Platform", platform_uuid)

# List all agents on that VOLTTRON platform
agents = api.list_agents(platform_uuid)

for agent in agents:
    # print(agent)
    # Check if listener agent is running
    if agent['identity'] in identity_list:
        if agent['is_running']:
            print("Stopping agent {}".format(agent['identity']))
            result = api.stop_agent(platform_uuid, [agent['uuid']])
            print (result)
