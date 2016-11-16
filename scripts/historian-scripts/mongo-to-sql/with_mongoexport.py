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
from datetime import datetime, timedelta
import pytz
import subprocess
from csv import DictReader
from StringIO import StringIO

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
class MongodbToSQLHistorian:
    def __init__(self, config_path, topic_pattern, start_time, end_time, **kwargs):
        self.mongodbclient = None
        self._topic_collection = 'topics'
        self._meta_collection = 'meta'
        self._data_collection = 'data'
        self._mongo_topic_id_map = {}
        self._sqldbclient = None
        self._sql_topic_id_map = {}
        self._sql_topic_name_map = {}
        self._mongo_to_sql_topic_id = {}
        self._topic_prefix_pattern = topic_pattern
        self._time_period = '1M'
        self._hosts = ''
        self._db_name = ''
        self._user = ''
        self._passwd = ''
        self._authsource = ''
        #Check and set the start and end time for data query
        #self.check_time_format(start_time, end_time)
        self._start_time = start_time
        self._end_time = end_time
        _log.info("Start time: {0}, End Time: {1}".format(self._start_time, self._end_time))
        self.db_config = None
        with open(config_path) as f:
            self.db_config = parse_json_config(f.read())
        #Set up remote Mongo DB and local SQLite DB connections
        self.mongodb_setup()
        self.sqldb_setup(self.db_config)

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

    def copy_from_mongo_to_sqllite(self):
        _log.info("Running Query for Topics Table")
        #Export Topics table
        topics_pattern = self._topic_prefix_pattern.replace('/', '\/')
        query_pattern = {'topic_name': {'$regex': topics_pattern, '$options': 'i'}}
        topics_query_pattern = str(query_pattern)
        outfile = 'topics.json'
        subprocess.call(["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase", self._authsource,
                         "--username", self._user, "--password", self._passwd, "--collection", self._topic_collection, "--query",
                         topics_query_pattern, "--out", outfile])
        #Dump topics table into SQLite
        _log.info("Dumping topics into SQLite")
        self._mongo_topic_id_map, topic_name_map = self.dump_topics_to_sqldb()
        topic_ids = self._mongo_topic_id_map.values()
        # Export Meta table
        _log.info("Running Query for Meta Table {}".format(len(topic_ids)))
        #self.process_meta_table_entries(topic_ids)
        self.process_data_table_entries(topic_ids)

    def process_meta_table_entries(self, topic_ids):
        metafilenames = []
        args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
                self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
                self._meta_collection, "--query", "", "--out", ""]
        i = 0
        if len(topic_ids) <= 2000:
            query_pattern = {'topic_id': {"$in": topic_ids}}
            meta_query_pattern = str(query_pattern)
            outfile = 'meta' + str(i) + '.json'
            args[14] = meta_query_pattern
            args[16] = outfile
            print("Mongodb export args: {}".format(args))
            subprocess.call(args)
        else:
            chk_cnt = int(len(topic_ids) / 2000)
            cnk_addl = len(topic_ids) % 2000
            for i in range(chk_cnt):
                new_list = topic_ids[i * 2000: (i + 1) * 2000 - 1]
                print("len: {0}, start: {1}, end: {2}".format(len(new_list), i * 2000, (i + 1) * 2000 - 1))
                outfile = 'meta' + str(i) + '.json'
                query_pattern = {'topic_id': {"$in": new_list}}
                meta_query_pattern = str(query_pattern)
                metafilenames.append(outfile)
                args[14] = meta_query_pattern
                args[16] = outfile
                print("Mongodb export args: {}".format(args))
                subprocess.call(args)
            new_list = topic_ids[(i + 1) * 2000:]
            print("len: {}".format(len(new_list)))
            outfile = 'meta' + str(i + 1) + '.json'
            query_pattern = {'topic_id': {"$in": new_list}}
            meta_query_pattern = str(query_pattern)
            metafilenames.append(outfile)
            args[14] = meta_query_pattern
            args[16] = outfile
            print("Mongodb export args: {}".format(args))
            subprocess.call(args)
        _log.info("Dumping Meta into SQLite")
        for f in metafilenames:
            self.dump_meta_to_sqldb(f)

    def process_data_table_entries(self, topic_ids):
        args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
                self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
                self._data_collection, "--query", "", "--out", ""]
        last = False
        next_compute_time = self._end_time
        i = 1
        _log.info("Running Query for Data Table")
        data_collection = 'data'
        ps = []
        datafilenames = []
        while not last:
            # Compute time slice
            start_time, end_time, last = self.compute_next_collection_time(next_compute_time, self._time_period)
            start_time_string = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
            end_time_string = end_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
            _log.info("Slice {0}: Start: {1}, End: {2}".format(i, start_time_string, end_time_string))
            if len(topic_ids) <= 2000:
                outfile = 'data' + str(i) + '.json'
                datafilenames.append(outfile)

                # Dump data table into SQLite DB for a time slice
                # query_pattern = {"ts": {"$gte": {"$date": "2016-01-28T20:18:50.000Z"}, "$lt": {"$date": "2016-01-28T20:38:50.000Z"}}}
                query_pattern = {"$and": [{"topic_id": {"$in": topic_ids}}, {
                    "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
                # query_pattern = {"ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}
                data_query_pattern = str(query_pattern)
                args[14] = data_query_pattern
                args[16] = outfile
                # print("query: {}".format(data_query_pattern))
                p = subprocess.Popen(args)
                ps.append(p)
            else:
                chk_cnt = int(len(topic_ids) / 2000)
                cnk_addl = len(topic_ids) % 2000
                j = 0
                for j in range(chk_cnt):
                    outfile = 'data' + str(i) + str(j) + '.json'
                    datafilenames.append(outfile)
                    new_list = topic_ids[j*2000: (j+1)*2000 - 1]
                    print("len: {0}, start: {1}, end: {2}".format(len(new_list), j * 2000, (j + 1) * 2000 - 1))
                    query_pattern = {"$and": [{"topic_id": {"$in": new_list}}, {
                        "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
                    data_query_pattern = str(query_pattern)
                    # print("query: {}".format(data_query_pattern))
                    data_query_pattern = str(query_pattern)
                    args[14] = data_query_pattern
                    args[16] = outfile
                    p = subprocess.Popen(args)
                    ps.append(p)
                #Final chunk
                new_list = topic_ids[(j + 1) * 2000:]
                outfile = 'data' + str(i) + str(j+1) + '.json'
                datafilenames.append(outfile)
                print("len: {}".format(len(new_list)))
                query_pattern = {"$and": [{"topic_id": {"$in": new_list}}, {
                    "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
                data_query_pattern = str(query_pattern)
                args[14] = data_query_pattern
                args[16] = outfile
                #print("mongdbexport: {}".format(args))
                p = subprocess.Popen(args)
                ps.append(p)
            next_compute_time = start_time
            i += 1
        for p in ps:
            p.wait()
        for f in datafilenames:
            self.dump_data_to_sqldb_in_chunk(f)

    '''Writes a topic into topics table of SQLite DB'''
    def dump_topics_to_sqldb(self):
        topic_id_map = {}
        topic_name_map = {}
        with open('topics.json', 'rb') as topicsfile:
            for row in topicsfile:
                data = jsonapi.loads(row)
                topic = data['topic_name']
                topic_lower = data['topic_name'].lower()
                #print("Topic name: {}".format(topic_lower))
                topic_id_map[topic_lower] = data['_id']
                topic_name_map[topic_lower] = \
                    data['topic_name']
                self.dump_topics(topic_lower)
                #print("Topic id: {}".format(topic_id_map[topic_lower]))
                self._mongo_to_sql_topic_id[topic_id_map[topic_lower]['$oid']] = self._sql_topic_id_map[topic_lower]
        return topic_id_map, topic_name_map

    def dump_topics(self, topic):
        # look at the topics that are stored in the database
        # already to see if this topic has a value
        topic_id = self._sql_topic_id_map.get(topic, None)
        db_topic_name = self._sql_topic_name_map.get(topic,
                                                None)
        if topic_id is None:
            # Insert topic name as is in db
            #row = self._sqldbclient.insert_topic(topic)
            row = self._sqldbclient.insert_topic_into_sqllite(topic)
            topic_id = row[0]
            # user lower case topic name when storing in map
            # for case insensitive comparison
            self._sql_topic_id_map[topic] = topic_id
            self._sql_topic_name_map[topic] = topic
            #_log.debug('TopicId: {} => {}'.format(topic_id, topic))
        elif db_topic_name != topic:
            _log.debug('Updating topic: {}'.format(topic))
            self._sqldbclient.update_topic_into_sqllite(topic, topic_id)
            self._sql_topic_name_map[topic] = topic

    '''Runs a query on the meta table in MongoDB for list of topic ids and writes the result into SQLite DB'''
    def dump_meta_to_sqldb(self, input):
        with open(input, 'rb') as metafile:
            for row in metafile:
                data = jsonapi.loads(row)
                # _log.info("meta data: {0} {1}".format(row['meta'], row['topic_id']))
                sql_topic_id = self._mongo_to_sql_topic_id[data['topic_id']['$oid']]
                self._sqldbclient.insert_meta_into_sqllite(sql_topic_id, data['meta'])

    def dump_data_to_sqldb_in_chunk(self, input):
        with open(input, 'rb') as datafile:
            for row in datafile:
                data = jsonapi.loads(row)
                # _log.info("meta data: {0} {1}".format(row['meta'], row['topic_id']))
                sql_topic_id = self._mongo_to_sql_topic_id[data['topic_id']['$oid']]
                #print("ts: {0}, {1}, {2}".format(data['ts'], sql_topic_id, data['value']))
                self._sqldbclient.insert_data_into_sqllite(data['ts']['$date'], sql_topic_id, data['value'])

    def compute_next_collection_time(self, end_time, period):
        last = False
        period_int = int(period[:-1])
        unit = period[-1:]
        if unit == 'm':
            start_time = end_time - timedelta(minutes=period_int)
        elif unit == 'h':
            start_time = end_time - timedelta(hours=period_int)
        elif unit == 'd':
            start_time = end_time - timedelta(days=period_int)
        elif unit == 'w':
            start_time = end_time - timedelta(weeks=period_int)
        elif unit == 'M':
            period_int *= 30
            start_time = end_time - timedelta(days=period_int)
        else:
            raise ValueError(
                "Invalid unit {} for collection period. "
                "Unit should be m/h/d/w/M".format(unit))
        # To check
        if start_time <= self._start_time:
            last = True
            start_time = self._start_time
        return start_time, end_time, last

    '''Setup SQLite DB client'''
    def sqldb_setup(self, config):
        if not config or not isinstance(config, dict):
            raise ValueError("Configuration should be a valid json")
        tables_def = {"table_prefix": "",
                      "data_table": "data",
                      "topics_table": "topics",
                      "meta_table": "meta"
                      }
        table_names = dict(tables_def)

        self._sqldbclient = MySqlLiteFuncts(config['sqlliteconnection']['params'],
                                            table_names)
        self._sqldbclient.setup_historian_tables()
        topic_id_map, topic_name_map = self._sqldbclient.get_topic_map()
        if topic_id_map is not None:
            self._sql_topic_id_map.update(topic_id_map)
        if topic_name_map is not None:
            self._sql_topic_name_map.update(topic_name_map)

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
        self.data_table = None
        self.meta_table = None

        if table_names:
            self.data_table = table_names['data_table']
            self.topics_table = table_names['topics_table']
            self.meta_table = table_names['meta_table']
        super(MySqlLiteFuncts, self).__init__('sqlite3', **connect_params)

    def setup_tables(self):

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
        cursor.execute('''CREATE TABLE IF NOT EXISTS ''' + self.data_table +
                       ''' (ts timestamp NOT NULL,
                       topic_id INTEGER NOT NULL,
                       value_string TEXT NOT NULL,
                       UNIQUE(topic_id, ts))''')

        cursor.execute('''CREATE INDEX IF NOT EXISTS data_idx
                                    ON ''' + self.data_table + ''' (ts ASC)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS ''' + self.meta_table +
                       '''(topic_id INTEGER PRIMARY KEY,
                        metadata TEXT NOT NULL)''')

        _log.debug("Created data topics and meta tables")

        conn.commit()
        conn.close()

    def insert_meta_into_sqllite(self, topic_id, metadata):
        conn = sqlite3.connect(
            self.__database,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        #print("metadata: {0}, {1}".format(topic_id, metadata))
        if conn is None:
            return False

        cursor = conn.cursor()
        timestamp = get_aware_utc_now()
        cursor.execute(self.insert_meta_stmt(),
                       (topic_id, jsonapi.dumps(metadata)))
        row = [cursor.lastrowid]
        conn.commit()
        conn.close()
        return row

    def insert_data_into_sqllite(self, ts, topic_id, data):
        conn = sqlite3.connect(
            self.__database,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        if conn is None:
            return False

        cursor = conn.cursor()
        timestamp = get_aware_utc_now()
        cursor.execute(self.insert_data_stmt(),
                       (ts, topic_id, jsonapi.dumps(data)))
        row = [cursor.lastrowid]
        conn.commit()
        conn.close()
        return row

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

    def insert_data_stmt(self):
        return '''REPLACE INTO ''' + self.data_table + \
               '''  values(?, ?, ?)'''

    def insert_meta_stmt(self):
        return '''INSERT OR REPLACE INTO ''' + self.meta_table + \
               ''' values(?, ?)'''

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
    parser = ArgumentParser(description="Retreive the topics, data, meta table from mongo database"
                                        "and store in sqllite database")

    parser.add_argument("config_file", help="Config file containing the connection info of Mongo and SQLLite db")
    parser.add_argument("topic_string", help="topic query pattern")
    parser.add_argument("start_time", help="Start time for query. Format: yy-mm-ddTHH:MM:SS")
    parser.add_argument("end_time", help="End time for query. Format: yy-mm-ddTHH:MM:SS")
    parser.set_defaults(
        config_file='config.db',
        topic_string='campus/building',
        start_time= datetime.strptime(
            '2016-01-01T00:00:00',
            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc),
        end_time= datetime.utcnow().replace(tzinfo=pytz.utc),
    )

    args = parser.parse_args(args)
    print("Arguments: {0}, {1}, {2}, {3}".format(args.topic_string, args.config_file,args.start_time, args.end_time))
    input_check = True
    '''Check the time format of input parameters - start_time and end_time'''
    try:
        start_time = datetime.strptime(
            args.start_time,
            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
    except ValueError:
        # self._start_time = datetime.strptime(
        #     '2016-01-01T00:00:00',
        #     '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
        _log.error("Wrong time format for start time: {0}. Valid Time Format: {1}.".
                   format(args.start_time, '%Y-%m-%dT%H:%M:%S'))
        input_check = False
    try:
        end_time = datetime.strptime(
            args.end_time,
            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
    except ValueError:
        _log.error("Wrong time format for end time: {0}. Valid Time Format: {1}.".
                   format(args.end_time, '%Y-%m-%dT%H:%M:%S'))
        input_check = False
    try:
        if input_check == True:
            msdb = MongodbToSQLHistorian(args.config_file, args.topic_string, start_time, end_time)
            msdb.copy_from_mongo_to_sqllite()
        #msdb.dump_data_to_sqldb_in_chunk('data1.csv')
    except Exception as e:
        _log.exception('unhandled exception' + e.message)


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
