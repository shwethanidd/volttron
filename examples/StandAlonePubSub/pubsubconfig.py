import os
import sys

from volttron.platform import config, keystore
from volttron.platform.agent import utils

class PubSubConfig(object):
    def __init__(self):
        self.arg_parser = self._setup_arg_parser()

    def _setup_arg_parser(self):
        parser = config.ArgumentParser()
        parser.add_argument('--vip-address', metavar='ZMQADDR',
            help='ZeroMQ URL to bind for VIP connections')
        parser.add_argument('--keystore', metavar='FILE',
            help='use keystore from FILE')
        parser.add_argument('--topic', help='Pub/Sub TOPIC')
        parser.add_argument('--server-key', help='public key of server')
        return parser

    def setup(self):
        args = self.arg_parser.parse_args()

        # If stdout is a pipe, re-open it line buffered
        if utils.isapipe(sys.stdout):
            # Hold a reference to the previous file object so it doesn't
            # get garbage collected and close the underlying descriptor.
            stdout = sys.stdout
            sys.stdout = os.fdopen(stdout.fileno(), 'w', 1)

        publickey = None
        secretkey = None
        if args.keystore:
            keys = keystore.KeyStore(args.keystore)
            if not os.path.isfile(args.keystore):
                keys.generate()
            publickey = keys.public()
            secretkey = keys.secret()
            sys.stdout.write("Agent's public key: {}\n".format(publickey))
            sys.stdout.flush()

        args.publickey = publickey
        args.secretkey = secretkey
        return args

