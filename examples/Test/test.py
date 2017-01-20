from apiutils import *
import base64

api = APITester("http://127.0.0.1:8080/jsonrpc")

response = api.do_rpc("list_platforms")
assert len(response.json()['result']) > 0
jsondata = response.json()
# Specific platform not the same as vcp on the platform
platform_uuid = jsondata['result'][0]['uuid']

print("Platform", platform_uuid)

agents = api.list_agents(platform_uuid)
 
print (agents.json())


for agent in agents.json()['result']:
    print (agent)
    if agent['name'].startswith('listener'):
        result = api.stop_agent(platform_uuid, [agent['uuid']])
        print (result)
        result = api.remove_agent(platform_uuid, [agent['uuid']])
        print (result)

#with open('/home/jer/.volttron/packaged/listeneragent-3.0-py2-none-any.whl') as f:
with open('/home/volttron/.volttron2/packaged/listeneragent-3.2-py2-none-any.whl') as f:
    encoded = base64.b64encode(f.read())
    
       
    files =  [
                {
                    "file_name": "listeneragent-3.2-py2-none-any.whl",
                    "file": "data:application/octet-stream;base64,{}".format(encoded)
                }
            ]
          
       
    agents = api.install_agent(platform_uuid, files)
      
    print(agents)
    print ("thing", agents.json())

    agent_result = agents.json()
    uuid = agent_result['result']['uuid']
    print (uuid)
    result = api.start_agent(platform_uuid, uuid)
    print (result)
    # for agent in agents.json()['result']:
    #     print("Agent", agent)
    #     result = api.start_agent(platform_uuid, [agent['uuid']])
    #     print (result)


