from datetime import datetime, timedelta
import pytz
from argparse import ArgumentParser
import sys
from volttron.platform.agent import utils
from volttron.platform.agent.utils import parse_json_config
from volttron.platform.messaging import topics
from volttron.platform.dbutils import mongoutils
import subprocess
import pymongo
from volttron.platform.messaging import headers as headers_mod
from volttron.platform.vip.agent import Agent
from volttron.platform.keystore import KeyStore
from volttron.platform import get_address
import gevent
from zmq.utils import jsonapi
HEADER_NAME_DATE = headers_mod.DATE
import logging
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)

def DataCollector(db_config_path, device_config_path, start_time, end_time):
    _log.info("Start time: {0}, End Time: {1}".format(start_time, end_time))
    keystore = KeyStore()
    datapub = DataPublisher(db_config_path, device_config_path, address=get_address(), identity='DATA_PUBLISHER', publickey=keystore.public, secretkey=keystore.secret,
                       enable_store=False)
    event = gevent.event.Event()
    glet = gevent.spawn(datapub.core.run, event)
    event.wait(timeout=5)
    datapub.publish_data(start_time, end_time)

class DataPublisher(Agent):
    def __init__(self, db_config_path, device_config_path, **kwargs):
        super(DataPublisher, self).__init__(**kwargs)
        self._topics_collections = 'topics'
        self._meta_collections = 'meta'
        self._data_collections = 'data'
        self._meta = dict()
        self._device_topic_id_map = dict()
        self._data = dict()
        db_config = utils.load_config(db_config_path)
        # Connect to mongo db
        if not db_config or not isinstance(db_config, dict):
            raise ValueError("Configuration should be a valid json")
            # exit

        # Get MongoDB connection details
        connection = db_config.get('mongoconnection')
        params = connection["params"]
        self.mongodbclient = mongoutils.get_mongo_client(params)

        # Get device config
        device_config = utils.load_config(device_config_path)
        campus_building = dict((key, device_config['device'][key]) for key in ['campus', 'building'])
        sub_devices = isinstance(device_config['device']['unit'], dict)
        device_config = device_config['device']['unit']
        #self._interval = device_config['device']['publish_interval']
        self._device_names = []
        self._device_topics = []
        self._subdevice_names = []
        self._subdevice_topics = []

        for device_name in device_config:
            device_topic = topics.DEVICES_VALUE(campus=campus_building.get('campus'),
                                                building=campus_building.get('building'),
                                                unit=device_name,
                                                path='',
                                                point='all')
            self._device_names.append(device_name)
            self._device_topics.append(device_topic)
            if sub_devices:
                for subdevice in device_config[device_name]['subdevices']:
                    #self._subdevices_list.append(subdevice)
                    subdevice_topic = topics.DEVICES_VALUE(campus=campus_building.get('campus'),
                                                           building=campus_building.get('building'),
                                                           unit=device_name,
                                                           path=subdevice,
                                                           point='all')
                    subdevice_name = device_name + "/" + subdevice
                    self._subdevice_names.append(subdevice_name)
                    self._subdevice_topics.append(subdevice_topic)
        _log.debug("Device Names {}, Device topics: {}".format(self._device_names, self._device_topics))
        _log.debug("Sub Device Names {}, Sub Device topics: {}".format(self._subdevice_names, self._subdevice_topics))

    def publish_data(self, start_time, end_time):
        #find time chunks
        i = 0
        device_topic_ids = dict()
        #Build topic ids for each device
        for device_topic in self._device_topics:
            _, device_topic_pattern_all = device_topic.split('/', 1)
            topic, _ = device_topic_pattern_all.rsplit('/', 1)
            _log.debug("Topic {0}".format(topic))
            #Getting topic ids matching pattern from db
            self._build_topic_id_map(topic)

        #_log.debug("Topic ids from DB {}".format(self._device_topic_id_map))

        #Build meta data for topics
        for device_topic in self._device_topics:
            _, device_topic_pattern_all = device_topic.split('/', 1)
            topic, _ = device_topic_pattern_all.rsplit('/', 1)
            topic_ids = self._device_topic_id_map[topic]
            for pt, topic_id in topic_ids:
                try:
                    pt_meta = self._meta[topic]
                except KeyError:
                    self._meta[topic] = pt_meta = []

                meta = self._collect_meta_data(topic_id)
                pt_meta.append((pt, meta))

        #_log.debug("Meta data for the topic ids from DB {}".format(self._meta))
        start = start_time
        end = end_time
        # Collect data points/values for all devices
        for device_topic in self._device_topics:
            _, device_topic_pattern_all = device_topic.split('/', 1)
            topic, _ = device_topic_pattern_all.rsplit('/', 1)
            #ids = [id for pt, id in self._device_topic_id_map[topic]]
            #MongoExport
            self._collect_data_points2(topic, start, end)

        # for topic_pt, topic_id in self._device_topic_id_map.items():
        #     try:
        #         topic = topic_pt[0]
        #         pt = topic_pt[1]
        #         _log.debug("Topic Pt values: {0}, {1}".format(topic, pt))
        #         pt_values = self._data[topic]
        #     except KeyError:
        #         self._data[topic] = pt_values = []
        #     values = self._collect_data_points(topic_id, start, end)
        #     pt_values.append((pt, values))
        # _log.debug("Pt values: {}".format(pt_values))

        now = datetime.datetime.now().isoformat(' ')
        headers = {HEADER_NAME_DATE: now}
        all_publish_message = []
        pt_values = dict()
        meta = dict()

        # # Publish 'all' message for devices, sub devices to message bus
        # for topic_all in self._subdevice_topics:
        #     _, topic = topic_all.rsplit('/', 1)
        #     topic, all = topic.rsplit('/', 1)
        #     data = self._data[topic]
        #     for pt, values in data:
        #         pt_values[pt] = values.pop(0)
        #     for pt, mt in self._meta[topic]:
        #         meta[pt] = mt
        #     all_publish_message = [pt_values, meta]
        #     _log.debug("ALL message: {}".format(all_publish_message))
        # #Publish 'all' message for devices, sub devices to message bus
        # for topic_all in self._device_topics:
        #     _, topic = topic_all.rsplit('/', 1)
        #     topic, all = topic.rsplit('/', 1)
        #     data = self._data[topic]
        #     for pt, values in data:
        #         pt_values[pt] = values.pop(0)
        #     for pt, mt in self._meta[topic]:
        #         meta[pt] = mt
        #     all_publish_message = [pt_values, meta]
        #     _log.debug("ALL message: {}".format(all_publish_message))
        #     # self.vip.pubsub.publish(peer='pubsub',
        #     #                         topic=device_topic,
        #     #                         message=all_publish_message,  # [data, {'source': 'publisher3'}],
        #     #                         headers=headers).get(timeout=2)

        #Publish 'all' message for devices, sub devices to message bus
        for topic_all in self._device_topics:
            _, topic = topic_all.rsplit('/', 1)
            topic, all = topic.rsplit('/', 1)
            data = self._data[topic]
            for pt, values in data:
                pt_values[pt] = values.pop(0)
            for pt, mta in self._meta[topic]:
                meta[pt] = mta
            all_publish_message = [pt_values, meta]
            _log.debug("ALL message: {}".format(all_publish_message))
            # self.vip.pubsub.publish(peer='pubsub',
            #                         topic=device_topic,
            #                         message=all_publish_message,  # [data, {'source': 'publisher3'}],
            #                         headers=headers).get(timeout=2)
        #Publish 'all' message for devices, sub devices to message bus
        for topic_all in self._subdevice_topics:
            _, topic = topic_all.rsplit('/', 1)
            topic, all = topic.rsplit('/', 1)
            data = self._data[topic]
            for pt, values in data:
                pt_values[pt] = values.pop(0)
            for pt, mt in self._meta[topic]:
                meta[pt] = mt
            all_publish_message = [pt_values, meta]
            _log.debug("ALL message: {}".format(all_publish_message))

    # def _collect_data_points(self, topic_ids, start, end):
    #     db = self.mongodbclient.get_default_database()
    #     mongo_data = dict()
    #     for tid in topic_ids:
    #         pattern = {"$and": [{'topic_id': tid}, {'ts': {"$gte": start, "$lt": end}}]}
    #         cursor = db[self._data_collections].find(pattern)#Todo sort according to ts
    #         values = []
    #         for num in xrange(cursor.count()):
    #             row = cursor[num]
    #             values = row['value']
    #         mongo_data[tid] = values
    #     return mongo_data

    """ db find with single topic id"""
    def _collect_data_points(self, topic_id, start, end):
        db = self.mongodbclient.get_default_database()

        pattern = {"$and": [{'topic_id': topic_id}, {'ts': {"$gte": start, "$lt": end}}]}
        cursor = db[self._data_collections].find(pattern)#Todo sort according to ts
        values = []
        for num in xrange(cursor.count()):
            row = cursor[num]
            values.append(row['value'])
        return values

    def _collect_data_points2(self, topic, start, end):
        db = self.mongodbclient.get_default_database()
        topic_ids = self._device_topic_id_map[topic].keys()
        pattern = {"$and": [{'topic_id': {"$in": topic_ids}}, {'ts': {"$gte": start, "$lt": end}}]}
        cursor = db[self._data_collections].find(pattern)#Todo sort according to ts
        pt_values= dict()
        try:
            pt_values = self._data[topic]
        except KeyError:
            self._data[topic] = pt_values = dict()
        values = []
        for num in xrange(cursor.count()):
            row = cursor[num]
            tid = row['topic_id']
            pt = self._device_topic_id_map[topic][tid]
            try:
                values = pt_values[pt]
            except KeyError:
                pt_values[pt] = values = []
            values.append(row['value'])

    def _collect_data_points(self, topic, start, end):
        args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
                self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
                self._data_collection, "--query", "", "--out", ""]
        outfile = 'data' + str(topic) + '.json'
        topic_ids = self._device_topic_id_map[topic].keys()
        # Dump data table into SQLite DB for a time slice
        # query_pattern = {"ts": {"$gte": {"$date": "2016-01-28T20:18:50.000Z"}, "$lt": {"$date": "2016-01-28T20:38:50.000Z"}}}
        query_pattern = {"$and": [{"topic_id": {"$in": topic_ids}}, {
            "ts": {"$gte": {"$date": start}, "$lt": {"$date": end}}}]}
        # query_pattern = {"ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}
        data_query_pattern = str(query_pattern)
        args[14] = data_query_pattern
        args[16] = outfile
        # print("query: {}".format(data_query_pattern))
        p = subprocess.Popen(args)
        p.wait()

    def read_data_from_file(self, topic, datafile):
        pt_values = dict()
        try:
            pt_values = self._data[topic]
        except KeyError:
            self._data[topic] = pt_values = dict()
        values = []
        with open(input, 'rb') as datafile:
            for row in datafile:
                data = jsonapi.loads(row)
                tid = data['topic_id']['$oid']
                pt = self._device_topic_id_map[topic][tid]
                try:
                    values = pt_values[pt]
                except KeyError:
                    pt_values[pt] = values = []
                values.append(data['value'])

    def _collect_meta_data(self, topic_id):
        db = self.mongodbclient.get_default_database()
        pattern = {'topic_id': topic_id}
        cursor = db[self._meta_collections].find(pattern)
        row = cursor[0]
        return row['meta']
        # meta = dict()
        # for num in xrange(cursor.count()):
        #     row = cursor[num]
        #     topic_id = row['topic_id']
        #     meta[topic_id] = row['meta']
        # return meta

    def _build_topic_id_map(self, topic_pattern):
        db = self.mongodbclient.get_default_database()
        topics_pattern = topic_pattern.replace('/', '\/')
        pattern = {'topic_name': {'$regex': topics_pattern, '$options': 'i'}}
        cursor = db[self._topics_collections].find(pattern)
        topic_ids = set()
        for document in cursor:
            topic, point = document['topic_name'].rsplit('/', 1)
            pt_topicid = dict()
            try:
                pt_topicid = self._device_topic_id_map[topic]
            except KeyError:
                self._device_topic_id_map[topic] = pt_topicid = dict()
            pt_topicid[document['_id']] = point

    def _get_device_data(self, topic_ids, start, end):
        db = self.mongodbclient.get_default_database()
        pattern = {"$and": [{'topic_id': {"$in": list(topic_ids)}}, {'ts': {"$gte": start, "$lt": end}}]}
        mongo_data = []
        cursor = db[self._data_collections].find(pattern)
        for num in xrange(cursor.count()):
            _log.info("num: {}".format(num))
            mongo_data.append(cursor[num])
        return mongo_data

def main(argv=sys.argv):
    args = argv[1:]
    parser = ArgumentParser(description="Retrieve the topics, data, meta table from mongo database"
                                        "and store in sqllite database")

    parser.add_argument("config_file", help="Config file containing the connection info of Mongo db")
    parser.add_argument("device_config_file", help="Config file for devices")
    parser.add_argument("start_time", help="Start time for query. Format: yy-mm-ddTHH:MM:SS")
    parser.add_argument("end_time", help="End time for query. Format: yy-mm-ddTHH:MM:SS")
    parser.set_defaults(
        config_file='config.db',
        device_config_file='test_config',
        start_time= datetime.strptime(
            '2016-01-01T00:00:00',
            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc),
        end_time= datetime.utcnow().replace(tzinfo=pytz.utc),
    )

    args = parser.parse_args(args)
    print("Arguments: {0}, {1}, {2}".format(args.config_file,args.start_time, args.end_time))
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
            dbcol = DataCollector(args.config_file, args.device_config_file, start_time, end_time)
    except Exception as e:
        _log.exception('unhandled exception' + e.message)


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())