# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright 2017, Battelle Memorial Institute.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This material was prepared as an account of work sponsored by an agency of
# the United States Government. Neither the United States Government nor the
# United States Department of Energy, nor Battelle, nor any of their
# employees, nor any jurisdiction or organization that has cooperated in the
# development of these materials, makes any warranty, express or
# implied, or assumes any legal liability or responsibility for the accuracy,
# completeness, or usefulness or any information, apparatus, product,
# software, or process disclosed, or represents that its use would not infringe
# privately owned rights. Reference herein to any specific commercial product,
# process, or service by trade name, trademark, manufacturer, or otherwise
# does not necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by
# BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
# }}}

from __future__ import absolute_import

import logging
import sys
import datetime

from volttron.platform.vip.agent import Agent, Core
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod

HEADER_NAME_DATE = headers_mod.DATE
HEADER_NAME_TIMESTAMP = headers_mod.TIMESTAMP
HEADER_NAME_CONTENT_TYPE = headers_mod.CONTENT_TYPE

utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = '0.1'

class ProsumerAgent(Agent):
    """Listens to everything and publishes a heartbeat according to the
    heartbeat period specified in the settings module.
    """

    def __init__(self, config_path, **kwargs):
        super(ProsumerAgent, self).__init__(**kwargs)
        self.counter = 0
        self.pt = []

    @Core.receiver('onstart')
    def onstart(self, sender, **kwargs):
        raise ValueError()
        # self.vip.pubsub.subscribe('pubsub', "utrc/vbm", self.on_match)
        # i=0
        # for i in range (0, 800):
        #     self.pt.append(i)

    @Core.periodic(30)
    def send_service_request(self):
        topic = "foo"
        frequency_range = [12, 13.5, 45, 67]
        response = 1
        regulation = 7.5
        ramping = 0
        self.counter = self.counter + 1
        message = dict(response=response,
                       regulation=regulation,
                       ramping=ramping,
                       frequency_range=self.pt,
                       data_id=self.counter)
        now = utils.format_timestamp(datetime.datetime.now())
        headers = {HEADER_NAME_DATE: now, HEADER_NAME_TIMESTAMP: now}
        _log.debug("Sending service request: {}".format(message))
        self.vip.pubsub.publish('pubsub', topic, headers=headers, message=message)


    def on_match(self, peer, sender, bus,  topic, headers, message):
        """Use match_all to receive all messages and print them out."""
        _log.debug("Incoming message from UTRC Matlab Driven agent"
        "Peer: %r, Sender: %r:, Bus: %r, Topic: %r, Headers: %r, Message: \n%s", peer, sender, bus, topic, headers, message)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(ProsumerAgent)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
