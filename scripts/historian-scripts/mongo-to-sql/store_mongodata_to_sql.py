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
import bson
import pymongo
import time
from volttron.platform.agent import utils
from argparse import ArgumentParser
from zmq.utils import jsonapi
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)

from volttron.platform.agent.utils import parse_json_config
from volttron.platform.vip.agent import Agent
from volttron.platform.dbutils import mongoutils
from volttron.platform.dbutils import sqlutils
from volttron.platform.dbutils.basedb import DbDriver
from volttron.platform.agent.utils import get_aware_utc_now
import threading
import os

description = """
This script retrieves all the topics in the "topics" table in MongoDb and
stores into SQLLite datbase

The script expects the target directory to have the following files and directories:
config_file         #Configuration file containing database connection details

The script expects the following as input parameter:
config_file         #Path of the Configuration file containing
                    database connection details
topic_string        #Topic pattern that needs to copied from MongoDb to SQLite
"""

class MongodbToSQLHistorian:
    def __init__(self, config_path, topic_pattern, **kwargs):
        self.mongodbclient = None
        self._topic_collection = 'topics'
        self.topic_id_map = {}
        self.dbfuncts_class = None
        self.sqlobj = None
        self.sql_topic_id_map = {}
        self.sql_topic_name_map = {}
        self.topic_prefix_pattern = topic_pattern
        with open(config_path) as f:
            db_config = parse_json_config(f.read())
        self.mongodb_setup(db_config)
        self.sqldb_setup(db_config)

    def mongodb_setup(self, config):
        if not config or not isinstance(config, dict):
            raise ValueError("Configuration should be a valid json")
        #Get MongoDB connection details
        connection = config.get('mongoconnection')
        self.mongodbclient = mongoutils.get_mongo_client(connection['params'])

    def copy_from_mongo_to_sqllite(self):
        self.topic_id_map, name_map = self.get_topic_by_pattern(self.topic_prefix_pattern)
        i = 0
        for topic_lower in name_map:
            print("Topic: {}".format(name_map[topic_lower]))
            self.write_to_sqldb(name_map[topic_lower])
            #self.commit_insertions()
        #self.commit_insertions()

    def sqldb_setup(self, config):
        if not config or not isinstance(config, dict):
            raise ValueError("Configuration should be a valid json")
        tables_def = {"table_prefix": "",
                      "data_table": "data",
                      "topics_table": "topics",
                      "meta_table": "meta",
                      "agg_topics_table": "agg_topics",
                      "agg_meta_table": "agg_meta"
                        }
        table_names = dict(tables_def)

        # 1. Check connection to db instantiate db functions class
        #connection = config.get('sqlliteconnection', None)
        # database_type = config['sqlliteconnection']['type']
        # db_functs_class = sqlutils.get_dbfuncts_class(database_type)
        # print("connecting to database {}".format(config['sqlliteconnection']['params']))
        # self.sqlobj = db_functs_class(config['sqlliteconnection']['params'],
        #                                table_names)
        #self.sqlobj.setup_historian_tables()
        self.sqlobj = MySqlLiteFuncts(config['sqlliteconnection']['params'],
                                      table_names)
        self.sqlobj.setup_historian_tables()
        topic_id_map, topic_name_map = self.sqlobj.get_topic_map()
        if topic_id_map is not None:
            self.sql_topic_id_map.update(topic_id_map)
        if topic_name_map is not None:
            self.sql_topic_name_map.update(topic_name_map)

    def commit_insertions(self):
        self.sqlobj.commit()

    #Returns dict of topics entries under topics table in Mongodb
    def get_topic_map(self, topics_collection):
        _log.debug("In get topic map")
        db = self.mongodbclient.get_default_database()
        #print("db: {}".format(db.getName()))
        cursor = db[topics_collection].find()
        topic_id_map = dict()
        topic_name_map = dict()
        for document in cursor:
            topic_id_map[document['topic_name'].lower()] = document['_id']
            topic_name_map[document['topic_name'].lower()] = \
                document['topic_name']
        _log.debug("Returning map from get_topic_map")
        return topic_id_map, topic_name_map

    #Returns dict of topics entries under topics table matching the query pattern in Mongodb
    def get_topic_by_pattern(self, pattern):
        topic_id_map, topic_name_map = self.find_topics_by_pattern(pattern)
        for topic_lower in topic_name_map:
            print("Patterned topic name: {0}".format(topic_name_map[topic_lower]))
        return topic_id_map, topic_name_map

    def find_topics_by_pattern(self, topics_pattern):
        db = self.mongodbclient.get_default_database()
        topics_pattern = topics_pattern.replace('/', '\/')
        pattern = {'topic_name': {'$regex': topics_pattern, '$options': 'i'}}
        #print("topics_pattern: {}".format(pattern))
        cursor = db[self._topic_collection].find(pattern)
        topic_id_map = dict()
        topic_name_map = dict()
        for document in cursor:
            topic_id_map[document['topic_name'].lower()] = document[
                '_id']
            topic_name_map[document['topic_name'].lower()] = \
                document['topic_name']
        return topic_id_map, topic_name_map

    def write_to_sqldb(self, topic):
        # look at the topics that are stored in the database
        # already to see if this topic has a value
        lowercase_name = topic.lower()
        topic_id = self.sql_topic_id_map.get(lowercase_name, None)
        db_topic_name = self.sql_topic_name_map.get(lowercase_name,
                                                None)
        if topic_id is None:
            # Insert topic name as is in db
            #row = self.sqlobj.insert_topic(topic)
            row = self.sqlobj.insert_topic_into_sqllite(topic)
            topic_id = row[0]
            # user lower case topic name when storing in map
            # for case insensitive comparison
            self.sql_topic_id_map[lowercase_name] = topic_id
            self.sql_topic_name_map[lowercase_name] = topic
            #_log.debug('TopicId: {} => {}'.format(topic_id, topic))
        elif db_topic_name != topic:
            _log.debug('Updating topic: {}'.format(topic))
            self.sqlobj.update_topic_into_sqllite(topic, topic_id)
            self.sql_topic_name_map[lowercase_name] = topic

def parse_json_config(config_str):
    """Parse a JSON-encoded configuration file."""
    return jsonapi.loads(utils.strip_comments(config_str))

""" SQLlite utility class """
class MySqlLiteFuncts(DbDriver):
    def __init__(self, connect_params, table_names):
        database = connect_params['database']
        thread_name = threading.currentThread().getName()
        _log.debug(
            "initializing sqlitefuncts in thread {}".format(thread_name))
        if database == ':memory:':
            self.__database = database
        else:

            self.__database = os.path.expandvars(os.path.expanduser(database))
            db_dir = os.path.dirname(self.__database)

            # If the db does not exist create it in case we are started
            # before the historian.
            try:
                if db_dir == '':
                    db_dir = './data'
                    self.__database = os.path.join(db_dir, self.__database)

                os.makedirs(db_dir)
            except OSError as exc:
                if exc.errno != errno.EEXIST or not os.path.isdir(db_dir):
                    raise

        connect_params['database'] = self.__database

        if 'detect_types' not in connect_params.keys():
            connect_params['detect_types'] = \
                sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES

        print (connect_params)
        self.topics_table = None

        if table_names:
            self.topics_table = table_names['topics_table']
        super(MySqlLiteFuncts, self).__init__('sqlite3', **connect_params)

    def setup_historian_tables(self):

        conn = sqlite3.connect(
            self.__database,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS ''' +
                       self.topics_table +
                       ''' (topic_id INTEGER PRIMARY KEY,
                            ts timestamp NOT NULL,
                            topic_name TEXT NOT NULL,
                            UNIQUE(ts, topic_name))''')
        _log.debug("Created data topics and meta tables")

        conn.commit()
        conn.close()


    def insert_topic_into_sqllite(self, topic):
        conn = sqlite3.connect(
            self.__database,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        if conn is None:
            return False

        cursor = conn.cursor()
        timestamp = get_aware_utc_now()
        cursor.execute(self.insert_topic_stmt(),
                       (timestamp, topic,))
        row = [cursor.lastrowid]
        conn.commit()
        conn.close()
        return row

    def update_topic_into_sqllite(self, topic):
        conn = sqlite3.connect(
            self.__database,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        if conn is None:
            return False

        cursor = conn.cursor()
        timestamp = get_aware_utc_now()
        cursor.execute(self.update_topic_stmt(),
                       (timestamp, topic,))
        row = [cursor.lastrowid]
        conn.commit()
        conn.close()
        return row

    def insert_topic_stmt(self):
        return '''INSERT INTO ''' + self.topics_table + \
               ''' (ts, topic_name) values (?, ?)'''

    def update_topic_stmt(self):
        return '''UPDATE ''' + self.topics_table + ''' SET topic_name = ?, ts = ?
            WHERE topic_id = ?'''

    def get_topic_map(self):
        _log.debug("in get_topic_map")
        q = "SELECT topic_id, topic_name FROM " + self.topics_table
        rows = self.select(q, None)
        _log.debug("loading topic map from db")
        id_map = dict()
        name_map = dict()
        for t, n in rows:
            id_map[n.lower()] = t
            name_map[n.lower()] = n
        return id_map, name_map

def main(argv=sys.argv):
    args = argv[1:]
    parser = ArgumentParser(description="Retreive the topics data from mongo database"
                                        "and store in sqllite database")
    # parser.add_argument(
    #     '-f', '--file', metavar='FILE', dest = "config_file",
    #     help='Config file containing the connection info of Mongo and SQLLite db')
    parser.add_argument("config_file", help="Config file containing the connection info of Mongo and SQLLite db")
    parser.add_argument("topic_string", help="topic query pattern")

    parser.set_defaults(
        config_file='config.db',
        topic_string='',
    )

    args = parser.parse_args(args)
    try:
        #utils.vip_main(MongodbToSQLHistorian)
        print("config file name: {}".format(args.config_file))
        msdb = MongodbToSQLHistorian(args.config_file, args.topic_string)
        msdb.copy_from_mongo_to_sqllite()
    except Exception as e:
        _log.exception('unhandled exception' + e.message)


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())