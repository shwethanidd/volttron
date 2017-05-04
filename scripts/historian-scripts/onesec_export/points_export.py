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
#import bson
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
class MongodbExport:
    def __init__(self, config_path, topic_pattern, start_time, end_time, **kwargs):
        self.mongodbclient = None
        self._topic_collection = 'topics'
        self._meta_collection = 'meta'
        self._data_collection = 'data'
        self._mongo_topic_id_map = {}
        self._topic_prefix_pattern = topic_pattern
        self._time_period = '1d'
        self._hosts = ''
        self._db_name = ''
        self._user = ''
        self._passwd = ''
        self._authsource = ''
        #Check and set the start and end time for data query
        self._start_time = start_time
        self._end_time = end_time
        _log.info("Start time: {0}, End Time: {1}".format(self._start_time, self._end_time))
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
        points = self.db_config.get('points')
        self._points = points["pt"]
        _log.debug("points: {}".format(self._points))

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
        #topic_ids = self._mongo_topic_id_map.values()
        # # Export Meta table
        # _log.info("Export Meta collection ")
        # self.process_meta_table_entries(topic_ids)
        # _log.info("Export Data collection {}".format(len(topic_ids)))
        topic_ids = self._get_topic_ids()
        _log.debug("Topic ids for points: {}".format(topic_ids))
        self.process_data_table_entries(topic_ids)

    def process_meta_table_entries(self, topic_ids):
        metafilenames = []
        args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
                self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
                self._meta_collection, "--query", "", "--out", ""]
        i = 1
        if len(topic_ids) <= 3000:
            query_pattern = {'topic_id': {"$in": topic_ids}}
            meta_query_pattern = str(query_pattern)
            outfile = 'meta' + str(i) + '.json'
            metafilenames.append(outfile)
            args[14] = meta_query_pattern
            args[16] = outfile
            # print("Mongodb export args: {}".format(args))
            subprocess.call(args)
        else:
            chk_cnt = int(len(topic_ids) / 3000)
            cnk_addl = len(topic_ids) % 3000
            for i in range(chk_cnt):
                new_list = topic_ids[i * 3000: (i + 1) * 3000 - 1]
                # print("len: {0}, start: {1}, end: {2}".format(len(new_list), i * 3000, (i + 1) * 3000 - 1))
                outfile = 'meta' + str(i) + '.json'
                query_pattern = {'topic_id': {"$in": new_list}}
                meta_query_pattern = str(query_pattern)
                metafilenames.append(outfile)
                args[14] = meta_query_pattern
                args[16] = outfile
                # print("Mongodb export args: {}".format(args))
                subprocess.call(args)
            new_list = topic_ids[(i + 1) * 3000:]
            # print("len: {}".format(len(new_list)))
            outfile = 'meta' + str(i + 1) + '.json'
            query_pattern = {'topic_id': {"$in": new_list}}
            meta_query_pattern = str(query_pattern)
            metafilenames.append(outfile)
            args[14] = meta_query_pattern
            args[16] = outfile
            print("Mongodb export args: {}".format(args))
            subprocess.call(args)

    def _get_topic_ids(self):
        topic_ids = []
        for point in self._points:
            topic_name = self._topic_prefix_pattern + '/' + point
            for name, id in self._mongo_topic_id_map.items():
                _log.debug("name: {0}, topic: {1}".format(name, topic_name))
                if name.lower() == topic_name.lower():
                    topic_ids.append(id)
                    break
        return topic_ids

    def process_data_table_entries(self, topic_ids):
        args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
                self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
                self._data_collection, "--query", "", "--type", "csv", "--fields", "ts,value,topic_id",
                "--out", ""]
        last = False
        next_compute_time = self._start_time
        i = 1
        _log.info("Running Query for Data Table")
        data_collection = 'data'
        ps = []
        datafilenames = []
        while not last:
            # Compute time slice
            start_time, end_time, last = self._compute_collection_slot(next_compute_time, self._end_time, self._time_period)
            start_time_string = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
            end_time_string = end_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
            _log.info("Slice {0}: Start: {1}, End: {2}".format(i, start_time_string, end_time_string))
            if len(topic_ids) <= 3000:
                 # Dump data table into SQLite DB for a time slice
                # query_pattern = {"ts": {"$gte": {"$date": "2016-01-28T20:18:50.000Z"}, "$lt": {"$date": "2016-01-28T20:38:50.000Z"}}}
                query_pattern = {"$and": [{"topic_id": {"$in": topic_ids}}, {
                    "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
                args[14] = str(query_pattern)
                outfile = 'data_' + start_time.strftime('%Y-%m-%d') + '.csv'
                datafilenames.append(outfile)
                args[20] = outfile
                #print("query: {}".format(args))
                p = subprocess.Popen(args)
                ps.append(p)
            else:
                chk_cnt = int(len(topic_ids) / 3000)
                cnk_addl = len(topic_ids) % 3000
                j = 0
                for j in range(chk_cnt):
                    outfile = 'data' + str(i) + str(j) + '.csv'
                    datafilenames.append(outfile)
                    new_list = topic_ids[j * 3000: (j + 1) * 3000 - 1]
                    # print("len: {0}, start: {1}, end: {2} outfile {3}".format(len(new_list), j * 3000, (j + 1) * 3000 - 1, outfile))
                    query_pattern = {"$and": [{"topic_id": {"$in": new_list}}, {
                        "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
                    data_query_pattern = str(query_pattern)
                    # print("query: {}".format(data_query_pattern))
                    args[14] = str(query_pattern)
                    args.append(outfile)
                    p = subprocess.Popen(args)
                    ps.append(p)
                # Final chunk
                new_list = topic_ids[(j + 1) * 3000:]
                outfile = 'data' + str(i) + str(j + 1) + '.json'
                datafilenames.append(outfile)
                # print("len: {0}, start: {1}, end: {2} outfile {3}".format(len(new_list), (j+1) * 3000, len(topic_ids),
                #                                                           outfile))
                query_pattern = {"$and": [{"topic_id": {"$in": new_list}}, {
                    "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
                data_query_pattern = str(query_pattern)
                args[14] = data_query_pattern
                args[16] = outfile
                # print("mongdbexport: {}".format(args))
                p = subprocess.Popen(args)
                ps.append(p)
            next_compute_time = end_time
            i += 1
        for p in ps:
            p.wait()

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

    def _compute_collection_slot(self, start_time, end, period):
        """
        Compute next time slot
        :param start_time: start time
        :param end: calculated end time
        :param period: slot period (in minutes, hour, days or month)
        :return: start and end time for time slot
        """
        last = False
        period_int = int(period[:-1])
        unit = period[-1:]
        if unit == 'm':
            end_time = start_time + timedelta(minutes=period_int)
        elif unit == 'h':
            end_time = start_time + timedelta(hours=period_int)
        elif unit == 'd':
            end_time = start_time + timedelta(days=period_int)
        elif unit == 'w':
            end_time = start_time + timedelta(weeks=period_int)
        elif unit == 'M':
            period_int *= 30
            end_time = start_time + timedelta(days=period_int)
        else:
            raise ValueError(
                "Invalid unit {} for collection period. "
                "Unit should be m/h/d/w/M".format(unit))
        # To check
        if end_time >= end:
            last = True
            end_time = end

        return start_time, end_time, last

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
            msdb = MongodbExport(args.config_file, args.topic_string, start_time, end_time)
            msdb.export_mongo_to_csv()
    except Exception as e:
        _log.exception('unhandled exception' + e.message)


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())