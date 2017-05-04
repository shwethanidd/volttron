# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2016, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those
# of the authors and should not be interpreted as representing official
# policies,
# either expressed or implied, of the FreeBSD Project.
#

# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

# }}}

from __future__ import absolute_import

import logging
import sys
import errno
import sqlite3

from volttron.platform.agent import utils
from argparse import ArgumentParser
from zmq.utils import jsonapi
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)

from volttron.platform.agent.utils import parse_json_config
from time import sleep
import os
import subprocess
import shutil

description = """
This script retrieves all the tables (topics, meta, data) in MongoDb and
stores into SQLLite datbase

The script expects the target directory to have the following files and directories:
config_file         #Configuration file containing database connection details

The script expects the following as input parameter:
config_file         #Path of the Configuration file containing
                    database connection details
topic_string        #Topic pattern that needs to copied from MongoDb to SQLite
start_time          #Start time for the data table query
end_time            #End time for the data table query
"""
class MongodbExport:
    def __init__(self, config_path, **kwargs):
        self.mongodbclient = None
        self._topic_collection = 'topics'
        self._meta_collection = 'meta'
        self._data_collection = 'data'
        self._mongo_topic_id_map = {}
        self._topic_prefix_pattern = ''
        self._hosts = ''
        self._db_name = ''
        self._user = ''
        self._passwd = ''
        self._authsource = ''
        self.db_config = None
        with open(config_path) as f:
            self.db_config = parse_json_config(f.read())
        #Set up remote Mongo DB
        self.mongodb_setup()

    def mongodb_setup(self):
        if not self.db_config or not isinstance(self.db_config, dict):
            raise ValueError("Configuration should be a valid json")
        # Get MongoDB connection details
        connection = self.db_config.get('mongoconnection')
        params = connection["params"]
        self._hosts = '{}:{}'.format(params["host"], params["port"])
        self._db_name = params["database"]
        self._topic_collection = 'topics'
        self._user = params['user']
        self._passwd = params['passwd']
        self._authsource = params['authSource']
        self._start_time = self.db_config.get('start-time')
        self._end_time = self.db_config.get('end-time')
        self._time_period = self.db_config.get('scrape-interval')
        self._topic_prefix_pattern = self.db_config.get('topic')

    def export_mongo_to_csv(self):
        _log.info("Running Query for Topics Table")
        #Export Topics table
        topics_pattern = self._topic_prefix_pattern.replace('/', '\/')
        topics_pattern = topics_pattern
        query_pattern = {'topic_name': {'$regex': topics_pattern, '$options': 'i'}}
        topics_query_pattern = str(query_pattern)
        outfile = 'topics.json'

        subprocess.call(["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase", self._authsource,
                         "--username", self._user, "--password", self._passwd, "--collection", self._topic_collection, "--query",
                         topics_query_pattern, "--out", outfile])
        #Read topic ids
        self._mongo_topic_id_map, topic_name_map = self._read_topics_json(outfile)
        #_log.debug("Topic ids: {}, topic map: {}".format(self._mongo_topic_id_map, topic_name_map))
        topic_ids = self._mongo_topic_id_map.values()
        topic_names = self._mongo_topic_id_map.keys()
        ps = []

        i = 0
        count = len(topic_ids)
        _log.debug("Number of Topic Ids to export {}".format(len(topic_ids)))
        while len(topic_ids) > 0:
            id = topic_ids.pop()
            name = topic_names.pop()
            p, file = self.export_data(name, id)
            item = dict(process=p, filename=file)
            ps.append(item)
            sleep(2)

        for item in ps:
            p = item['process']
            f = item['filename']
            p.wait()
            _log.debug("Done with export {}, {} to export".format(i, count - i))

            _, original_exported_file = f.split('/', 1)
            new_exported_file = os.path.join("completed", original_exported_file)
            #new_exported_file = "completed/" + original_exported_file
            path, file = new_exported_file.rsplit('/', 1)
            if not os.path.exists(path):
                os.makedirs(path)
            shutil.move(f, new_exported_file)
            print("Moved {}".format(f))

        _log.debug("All Done")
        # if len(ps) > 0:
        #     for p in ps:
        #         p.wait()
        #     del ps[:]

    def export_data(self, topic, topicid):
        args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
                self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
                self._data_collection, "--query", "", "--type", "csv", "--fields", "ts,value,topic_id",
                "--sort", "{ts: 1}", "--out", ""]

        _log.info("Running Query for Data Table")
        data_collection = 'data'
        ps = []
        datafilenames = []

        query_pattern = {"topic_id": topicid}
        args[14] = str(query_pattern)

        #print("query: {}".format(args))
        filename = self._db_name + "-" + topicid['$oid']
        outfile = "export/{}.csv".format(topic)
        args[22] = outfile
        stdout = "log/{}.log".format(filename)
        stderr = "log/{}.err".format(filename)
        return subprocess.Popen(args, stdout=open(stdout, 'w'), stderr=open(stderr, 'w')), outfile

    def _read_topics_json(self, topic_ids_file):
        topic_id_map = {}
        topic_name_map = {}
        try:
            with open(topic_ids_file) as f:
                for row in f:
                    data = jsonapi.loads(row)
                    topic = data['topic_name']
                    topic_id_map[topic] = data['_id']
                    topic_name_map[topic] = data['topic_name']
        except IOError as ex:
            #_log.debug("File error: {}".format(ex))
            return {}, {}
        return topic_id_map, topic_name_map

def main(argv=sys.argv):
    args = argv[1:]
    parser = ArgumentParser(description="Retreive the topics, data, meta table from mongo database"
                                        "and store in sqllite database")

    parser.add_argument("config_file", help="Config file containing the connection info of Mongo and SQLLite db")
    parser.set_defaults(
        config_file='config.db'
    )

    args = parser.parse_args(args)
    print("Arguments: {0}".format(args.config_file))
    input_check = True
    '''Check the time format of input parameters - start_time and end_time'''

    try:
        msdb = MongodbExport(args.config_file)
        msdb.export_mongo_to_csv()
    # except ValueError:
    #     _log.exception('Input check failed')
    except Exception as e:
        _log.exception('unhandled exception' + e.message)

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())