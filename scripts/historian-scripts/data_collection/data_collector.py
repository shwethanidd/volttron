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
from collections import defaultdict
import gevent
from gevent.queue import Queue, Empty
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
    datapub.collect_publish_data(start_time, end_time)

class DataPublisher(Agent):
    def __init__(self, db_config_path, device_config_path, **kwargs):
        super(DataPublisher, self).__init__(**kwargs)
        self._topics_collections = 'topics'
        self._meta_collections = 'meta'
        self._data_collections = 'data'
        self._event_queue = Queue()

        def ids_pt():
            return defaultdict(str)

        def pt_meta():
            return defaultdict(dict)

        self._meta = defaultdict(pt_meta)
        self._topics = defaultdict(ids_pt)

        self._points = set()
        db_config = utils.load_config(db_config_path)
        # Connect to mongo db
        if not db_config or not isinstance(db_config, dict):
            raise ValueError("Configuration should be a valid json")
            # exit

        # Get MongoDB connection details
        connection = db_config.get('mongoconnection')
        params = connection["params"]
        self._hosts = '{}:{}'.format(params["host"], params["port"])
        self._db_name = params["database"]
        self._user = params['user']
        self._passwd = params['passwd']
        self._authsource = params['authSource']
        self._mongodbclient = mongoutils.get_mongo_client(params)

        # Get device config
        device_config = utils.load_config(device_config_path)
        campus_building = dict((key, device_config['device'][key]) for key in ['campus', 'building'])
        sub_devices = isinstance(device_config['device']['unit'], dict)
        points = dict()
        points = device_config['points']
        self._points = points.values()
        device_config = device_config['device']['unit']
        #self._interval = device_config['device']['publish_interval']
        self._device_names = []
        self._device_topics = []
        self._subdevice_names = []
        self._subdevice_topics = []
        self._db_topics = []

        for device_name in device_config:
            device_topic = topics.DEVICES_VALUE(campus=campus_building.get('campus'),
                                                building=campus_building.get('building'),
                                                unit=device_name,
                                                path='',
                                                point='all')
            self._device_names.append(device_name)
            self._device_topics.append(device_topic)
            _, topic_all = device_topic.split('/', 1)
            topic, _ = topic_all.rsplit('/', 1)
            self._db_topics.append(topic.lower())
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
                    _, topic_all = subdevice_topic.split('/', 1)
                    topic, _ = topic_all.rsplit('/', 1)
                    self._db_topics.append(topic.lower())
        _log.debug("Device Names {}, Device topics: {}".format(self._device_names, self._device_topics))
        _log.debug("Sub Device Names {}, Sub Device topics: {}".format(self._subdevice_names, self._subdevice_topics))
        _log.debug("DB topics: {}".format(self._db_topics))

    def collect_publish_data(self, start, end):
        #Set time period
        _log.debug("****************************************************************")
        _log.debug("COLLECTING TOPIC IDS")
        _log.debug("****************************************************************")
        self._collect_topic_ids()
        _log.debug("****************************************************************")
        _log.debug("COLLECTING META DATA")
        _log.debug("****************************************************************")
        self._collect_meta_data()
        self._device_topics.extend(self._subdevice_topics)
        glets = []
        #Greenlet 1:
        glets = [gevent.spawn(self._collect_data, start, end), gevent.spawn(self._publish_data)]
        gevent.joinall(glets)
        _log.debug("****************************************************************")
        _log.debug("DONE")
        _log.debug("****************************************************************")

    def _collect_topic_ids(self):
        device_topic_ids = dict()
        # Collect topic ids for each device
        for device_topic in self._device_topics:
            _, device_topic_pattern_all = device_topic.split('/', 1)
            topic, _ = device_topic_pattern_all.rsplit('/', 1)
            # Getting topic ids matching pattern from db
            self._get_topic_ids(topic)
            # _log.debug("Topic {0}, Topic IDs: {1}".format(topic, self._topics[topic]))
        #_log.debug("Topic ids from DB {}".format(self._topics))

    def _collect_meta_data(self):
        pt_meta = dict()
        for topic in self._topics:
            #_log.debug("COLLECTING META DATA for {}".format(topic))
            self._get_meta_data(topic)
            # _log.debug("Topic: {}, Meta from DB {}".format(topic, self._meta[topic]))
        _log.debug("Topic: {}, Meta from DB {}".format(topic, self._meta))

    def _collect_data(self, start, end):
        last = False
        time_period = '10d'
        next_compute_time = end
        while not last:
            # Compute time slice
            start_time, end_time, last = self.compute_collection_slot(start, next_compute_time, time_period)
            self._collect_time_slice_data(start_time, end_time)
            gevent.sleep(0.5)
            next_compute_time = start_time
        self._event_queue.put('Done')


    def _collect_time_slice_data(self, start, end):
        _log.debug("****************************************************************")
        _log.debug("COLLECTING DATA VALUES Time Slice {0} - {1}".format(start, end))
        _log.debug("****************************************************************")

        def pt_values():
            return defaultdict(list)
        data = defaultdict(pt_values)

        # Collect data point-values for all devices
        for topic in self._topics:
            # PyMongo find
            #_log.debug("COLLECTING DATA VALUES For DEVICE {0}, Time Slice {1} - {2}".format(topic, start, end))
            self._get_device_data(topic, data, start, end)
            #_log.debug("Data {}".format(self._data[topic]))
        if data:
            self._event_queue.put(data)
            gevent.sleep(10)
        else:
            _log.debug("No data to send")

    def _get_device_data(self, topic, data, start, end):
        db = self._mongodbclient.get_default_database()
        topic_ids = self._topics[topic]
        tids = list(topic_ids.keys())

        pattern = {"$and": [{'topic_id': {"$in": tids}}, {'ts': {"$gte": start, "$lt": end}}]}
        pipeline = [{"$match": pattern}, {"$sort": {"ts": 1}}]
        #pattern = {'topic_id': {"$in": tids}}
        cursor = db[self._data_collections].aggregate(pipeline)  # Todo sort according to ts
        #_log.debug("Pattern search: {}".format(pipeline))
        rows = list(cursor)
        for row in rows:
            _log.debug("Data row: {}".format(row))
            tid = row['topic_id']
            pt = self._topics[topic][tid]
            data[topic][pt].append(row['value'])

    def _get_meta_data(self, topic):
        db = self._mongodbclient.get_default_database()

        topic_ids = self._topics[topic]
        topic_ids = list(topic_ids.keys())

        #_log.debug("topic ids: {}".format(topic_ids))
        pattern = {'topic_id': {"$in": topic_ids}}
        cursor = db[self._meta_collections].find(pattern)
        for row in cursor:
            #_log.debug("row: {}".format(row))
            topic_id = row['topic_id']
            pt = self._topics[topic][topic_id]
            self._meta[topic][pt] = row['meta']

    def _get_topic_ids(self, topic_pattern):
        db = self._mongodbclient.get_default_database()
        topics_pattern = topic_pattern.replace('/', '\/')
        topics_pattern = '^' + topics_pattern
        pattern = {'topic_name': {'$regex': topics_pattern, '$options': 'i'}}
        cursor = db[self._topics_collections].find(pattern)

        #_log.debug("Topic pattern: {}".format(pattern))
        for document in cursor:
            topic, point = document['topic_name'].rsplit('/', 1)
            _log.debug("Topic {0}, point {1}".format(topic, point))
            pt = point.lower()
            topic = topic.lower()
            if topic in self._db_topics and pt in self._points:
                self._topics[topic][document['_id']] = point

    def _publish_data(self):
        _log.debug("****************************************************************")
        _log.debug("PUBLISH")
        _log.debug("****************************************************************")
        for msg in self._event_queue:
            if isinstance(msg, str):
                if msg == 'Done':
                    return
            else:
                now = datetime.now().isoformat(' ')
                headers = {HEADER_NAME_DATE: now}
                all_publish_message = []
                pt_values = dict()
                meta = dict()
                cnt = 0
                _log.debug("Device topics: {}".format(self._device_topics))
                _log.debug("Device topics: {}".format(msg))
                #Publish 'all' message for devices, sub devices to message bus
                for topic_all in self._device_topics:
                    _, topic = topic_all.split('/', 1)
                    topic, all = topic.rsplit('/', 1)
                    topic = topic.lower()
                    data = msg[topic]
                    if data:
                        try:
                            cnt = len(data.values()[0])
                            _log.debug("Data Topc: {0}, Cnt: {1}".format(topic, cnt))
                            mta = self._meta[topic]
                            i = 0
                            for i in xrange(cnt):
                                for pt, values in data.items():
                                    pt_values[pt] = values[i]
                                    meta[pt] = mta[pt]
                                all_publish_message = [pt_values, meta]
                                _log.debug("****************************************************************")
                                _log.debug(
                                    "ALL message for DEVICE: {0} is {1}, Iteration: {2}, Value Cnt: {3}".
                                        format(topic,
                                               all_publish_message,
                                               i,
                                               len(values)))
                                _log.debug("****************************************************************")
                                self.vip.pubsub.publish(peer='pubsub',
                                                        topic=topic_all,
                                                        message=all_publish_message,
                                                        headers=headers).get(timeout=2)
                                pt_values.clear()
                                meta.clear()
                        except IndexError:
                            _log.debug("Data for index error {}".format(topic))
                    else:
                        _log.debug("Data is empty: {}".format(topic))

    def compute_collection_slot(self, start, end_time, period):
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
        if start_time <= start:
            last = True
            start_time = start

        return start_time, end_time, last

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