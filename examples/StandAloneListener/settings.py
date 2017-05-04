# These topic will be watched.  The messages will be written to
# standard out.
topics_prefixes_to_watch = (
	'devices',
	#'datalogger'
)

heartbeat_period = 10

# The parameters dictionary is used to populate the agent's 
# remote vip address.
_params = {
	# The root of the address.
#	'vip_address': 'tcp://172.26.65.218',
        'vip_address': 'tcp://192.101.105.94',
	'port': 22916,

	# public and secret key for the standalonelistener agent.
	# These can be created from the volttron-ctl keypair command.
	'agent_public': 'w9VrC6Q1yqdIfj8ZQi_zmBMk4jaI86mTIw36-s9sDGc',
	'agent_secret': 'CtRNT4owNHW_8CYGViEvP_Sa5nA0OOIzMg3U-7NA8nA',
	
	# Public server key from the remote platform.  This can be
	# obtained from the starting of the platform volttron -v.
	# The output will include public key: ....
	'server_key': 'S-fmqYAx-WpJyUugOMTMOwv70P6jeo-Wr5ev0FTCTzc'
}

def remote_url():
	return "{vip_address}:{port}?serverkey={server_key}" \
		"&publickey={agent_public}&" \
		"secretkey={agent_secret}".format(**_params)
