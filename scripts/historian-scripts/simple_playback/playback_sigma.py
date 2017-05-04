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
import Queue
import time
# from gevent.queue import Queue, Empty

from zmq.utils import jsonapi
import threading
HEADER_NAME_DATE = headers_mod.DATE
import logging
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)

"""
The `pyclass:DataPlayback` is responsible for playback of device data for specified period of time on the message bus.

A default configuration for this agent is as follows.

.. code-block:: json
    {
        "mongoconnection": {
            "type": "mongodb",
            "params": {
                "host": "volttrondev.pnl.gov",
                "port": 27017,
                "database": "historian",
                "user": "historian",
                "passwd": "volttron",
                "authSource":"historian"
            }
        },
        #Should follow time format: yy-mm-ddTHH:MM:SS for example 2016-05-20T00:00:00
        "playback-start-time":"2016-05-20T00:00:00",
        #Should follow time format: yy-mm-ddTHH:MM:SS for example 2016-05-29T00:00:00
        "playback-end-time":"2016-05-29T00:00:00"
    }
"""


class DataPlayback(Agent):
    def __init__(self, db_config_path, device_topic, **kwargs):
        super(DataPlayback, self).__init__(**kwargs)
        self._topics_collections = 'topics'
        self._meta_collections = 'meta'
        self._data_collections = 'data'
        self._event_queue = Queue.Queue()

        def ids_point():
            return defaultdict(str)

        def point_meta():
            return defaultdict(dict)

        self._meta = defaultdict(point_meta)
        self._topics = defaultdict(ids_point)

        self._points = set()

        db_config = utils.load_config(db_config_path)
        # Connect to mongo db
        if not db_config or not isinstance(db_config, dict):
            raise ValueError("Configuration should be a valid json")
            # exit

        try:
            # Get MongoDB connection details
            connection = db_config.get('mongoconnection')
            params = connection["params"]
            self._hosts = '{}:{}'.format(params["host"], params["port"])
            self._db_name = params["database"]
            self._user = params['user']
            self._passwd = params['passwd']
            self._authsource = params['authSource']
            self._mongodbclient = mongoutils.get_mongo_client(params)
            self._playback_start = db_config['playback-start-time']
            self._playback_end = db_config['playback-end-time']

            #Get playback start and end time
            try:
                self._playback_start = datetime.strptime(
                    self._playback_start,
                    '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
            except ValueError:
                _log.error("Wrong time format for start time: {0}. Valid Time Format: {1}.".
                           format(self._playback_start, '%Y-%m-%dT%H:%M:%S'))
                raise ValueError("Wrong time format for playback start time: {0}. Valid Time Format: {1}.".
                           format(self._playback_start, '%Y-%m-%dT%H:%M:%S'))
            try:
                if self._playback_end == "":
                    self._playback_end = datetime.utcnow().replace(tzinfo=pytz.utc)
                else:
                    self._playback_end = datetime.strptime(
                        self._playback_end,
                        '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
            except ValueError:
                _log.error("Wrong time format for end time: {0}. Valid Time Format is: {1}.".
                           format(self._playback_end, '%y-%m-%dT%H:%M:%S'))
                raise ValueError("Wrong time format for playback end time: {0}. Valid Time Format is: {1}.".
                                 format(self._playback_end, '%y-%m-%dT%H:%M:%S'))


            self._device_topics = []
            self._device_topics.append(device_topic + '/all')
            self._subdevice_topics = []
            self._db_topics = []
            sub_devices = False
            _, topic = device_topic.split('/', 1)
            self._db_topics.append(topic.lower())
            self._db_topics = device_topic.lower()

            _log.debug("Device topics: {}".format(self._device_topics))
            _log.debug("DB topics: {}".format(self._db_topics))
        except KeyError:
            _log.error("Configuration parameter is missing")
            raise ValueError("Configuration parameter is missing")

    def playback_data(self):
        """
        Retrieve device data from mongo historian for the specified time period and publish on message bus.
        """
        _log.debug("****************************************************************")
        _log.debug("COLLECTING TOPIC IDS")
        _log.debug("****************************************************************")
        self._collect_topic_ids()
        _log.debug("****************************************************************")
        _log.debug("COLLECTING META DATA")
        _log.debug("****************************************************************")
        self._collect_meta_data()
        self._device_topics.extend(self._subdevice_topics)
        #self._mongoexport_all_db(self._playback_start, self._playback_end)
        stop_event = threading.Event()
        try:
            collection_thread = threading.Thread(target=self._collect_data, args=(stop_event, ))
            collection_thread.daemon = True
            collection_thread.start()
            publish_thread = threading.Thread(target=self._publish_data, args=(stop_event, ))
            publish_thread.daemon = True
            publish_thread.start()

            while True:
                time.sleep(1)
                publish_thread.join(60000)
                collection_thread.join(60000)
        except KeyboardInterrupt:
            stop_event.set()
            #collection_thread.join()
            # publish_thread.join()
            _log.debug("KEYBOARD INTERRUPT")
        # glets = [gevent.spawn(self._collect_data),
        #          gevent.spawn(self._publish_data)]
        # gevent.joinall(glets)
        _log.debug("****************************************************************")
        _log.debug("DONE")
        _log.debug("****************************************************************")

    def _collect_topic_ids(self):
        """
        Get topic ids for all the device topics
        :return:
        """
        # Collect topic ids for each device
        for device_topic in self._device_topics:
            _, device_topic_pattern_all = device_topic.split('/', 1)
            topic, _ = device_topic_pattern_all.rsplit('/', 1)
            _log.debug("device topic all: {0}, topic: {1}".format(device_topic, topic))
            # Getting topic ids matching pattern from db
            self._get_topic_ids(topic)
            #_log.debug("Topic {0}, Topic IDs: {1}".format(topic, self._topics[topic]))
        _log.debug("Topic ids from DB {}".format(self._topics))

    def _collect_meta_data(self):
        """
        Get meta data associated with device topics
        :return:
        """
        pt_meta = dict()
        for topic in self._topics:
            #_log.debug("COLLECTING META DATA for {}".format(topic))
            self._get_meta_data(topic)
            # _log.debug("Topic: {}, Meta from DB {}".format(topic, self._meta[topic]))
        _log.debug("Topic: {}, Meta from DB {}".format(topic, self._meta))

    def _collect_data(self, stop_event):
        """
        Get device data for all devices (and sub devices) in time chunks. Collected data is put in event queue
        for publishing.
        :return:
        """
        start = self._playback_start
        end = self._playback_end
        last = False
        time_period = '1d'
        next_compute_time = start

        while not last and not stop_event.is_set():
            # Compute time slice. Tentatively 1 day time slice
            start_time, end_time, last = self._compute_collection_slot(next_compute_time, end, time_period)
            _log.debug("Last: {}".format(last))
            self._collect_time_slice_data(start_time, end_time)
            gevent.sleep(2)
            next_compute_time = end_time
        self._event_queue.put('Done')
        _log.debug("****************************************************************")
        _log.debug("COLLECTION: DONE")
        _log.debug("****************************************************************")


    def _collect_time_slice_data(self, start, end):
        """
        Retrieve device data for all device (and sub devices) for particular time slot. Add the collected data into
        event queue
        :param start: start time
        :param end: end time
        :return:
        """
        _log.debug("****************************************************************")
        _log.debug("COLLECTION: DATA VALUES Time Slice {0} - {1}".format(start, end))
        _log.debug("****************************************************************")

        def point_values():
            return defaultdict(list)
        data = defaultdict(point_values)

        # Collect point-values for all devices
        for topic in self._topics:
            _log.debug("COLLECTING DATA VALUES For DEVICE {0}, Time Slice {1} - {2}".format(topic, start, end))
            self._get_device_data(topic, data, start, end)
        if data:
            msg = dict(start = start, end= end, data= data)
            self._event_queue.put(msg)
        else:
            _log.debug("No data to send")

    def _get_device_data(self, topic, data, start, end):
        """
        Get device data from from mongo db
        :param topic: device topic
        :param data: device data
        :param start: start time
        :param end: end time
        :return:
        """
        db = self._mongodbclient.get_default_database()
        topic_ids = self._topics[topic]
        tids = list(topic_ids.keys())

        pattern = {"$and": [{'topic_id': {"$in": tids}}, {'ts': {"$gte": start, "$lt": end}}]}

        project = {"_id": 0, "timestamp": {
            '$dateToString': {'format': "%Y-%m-%dT%H:%M:%S",
                              "date": "$ts"}}, "value": 1, "topic_id": 1}
        pipeline = [{"$match": pattern}, {"$sort": {"ts": 1}}, {"$project": project}]

        cursor = db[self._data_collections].aggregate(pipeline)

        rows = list(cursor)
        #_log.debug("Rows for topic {0} is: {1}".format(topic, len(rows)))
        for row in rows:
            #_log.debug("Data row: {0}, topic: {1}".format(row, topic))
            tid = row['topic_id']
            point = self._topics[topic][tid]
            data[topic][point].append((row['timestamp'], row['value']))

    def _get_meta_data(self, topic):
        """
        Get meta data for the topic from mongo db
        :param topic: device topic
        :return:
        """
        db = self._mongodbclient.get_default_database()

        topic_ids = self._topics[topic]
        topic_ids = list(topic_ids.keys())

        #_log.debug("topic ids: {}".format(topic_ids))
        pattern = {'topic_id': {"$in": topic_ids}}
        cursor = db[self._meta_collections].find(pattern)
        for row in cursor:
            #_log.debug("row: {}".format(row))
            topic_id = row['topic_id']
            point = self._topics[topic][topic_id]
            self._meta[topic][point] = row['meta']

    def _get_topic_ids(self, topic_pattern):
        """
        Get topic ids matching the topic pattern
        :param topic_pattern: topic
        :return:
        """
        db = self._mongodbclient.get_default_database()
        topics_pattern = topic_pattern.replace('/', '\/')
        topics_pattern = '^' + topics_pattern
        pattern = {'topic_name': {'$regex': topics_pattern, '$options': 'i'}}
        cursor = db[self._topics_collections].find(pattern)

        #_log.debug("Topic pattern: {}".format(pattern))
        for document in cursor:
            topic, point = document['topic_name'].rsplit('/', 1)
            pt = point.lower()
            topic = topic.lower()
            #_log.debug("Topic {0}, point {1}".format(topic, point))
            if topic in self._db_topics:
                self._topics[topic][document['_id']] = point

    def _publish_data(self, stop_event):
        """
        Publish messages available in event queue
        :return:
        """
        _log.debug("****************************************************************")
        _log.debug("PUBLISH")
        _log.debug("****************************************************************")
        keep_going = True
        while keep_going or not stop_event.is_set():
            msg = self._event_queue.get()
            if isinstance(msg, str):
                if msg == 'Done':
                    keep_going = False
            else:
                if isinstance(msg, dict):
                    self._publish_data_chunk(msg)
        _log.debug("PUBLISH DONE")

    def _publish_data_chunk(self, msg):
        """
        Publish all message in sequence
        :param msg:
        :return:
        """
        time_slot_start = msg['start']
        time_slot_end = msg['end']
        data = msg['data']
        start = time_slot_start
        now = datetime.now().isoformat(' ')

        #Header time stamp will be changed later to contain actual device data time stamp
        headers = {HEADER_NAME_DATE: now}
        all_publish_message = []
        pt_values = dict()
        meta = dict()
        device_publish_status = dict()
        cnt = 0
        done = False

        # Form 'all' message for each device (and sub device) and publish to message bus
        for topic_all in self._device_topics:
            _, topic = topic_all.split('/', 1)
            topic, all = topic.rsplit('/', 1)
            topic = topic.lower()
            device_publish_status[topic] = False

        #Iterate through entire time slot in increments of 1 minute
        while start != time_slot_end and not done:
            end = start + timedelta(minutes=1)
            _log.debug("****************************************************************")
            _log.debug("PUBLISH: Time slice: {0} - {1}".format(start, end))
            _log.debug("****************************************************************")

            #Form 'all' message for each device (and sub device) and publish to message bus
            for topic_all in self._device_topics:
                _, topic = topic_all.split('/', 1)
                topic, all = topic.rsplit('/', 1)
                topic = topic.lower()
                playback_data = data[topic]

                if playback_data:
                    is_send = True
                    for point, values in playback_data.iteritems():
                        if values:
                            ts, val = values[0]
                            #Format the timestamp into UTC
                            ts = datetime.strptime(
                                ts,
                                '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
                            # _log.debug("Time stamp: DB TS: {0}, LEN: {1}, Topic: {2}".
                            #            format(ts, len(values), topic))
                            #If ts matches the correct publish period, then add to 'all' message else discard
                            if ts >= start and ts <= end:
                                pt_values[point] = val
                                meta[point] = self._meta[topic][point]
                            else:
                                is_send= False
                                break
                        else:
                            device_publish_status[topic] = True
                            is_send = False
                    if is_send:
                        #Pop value out
                        for point, values in playback_data.iteritems():
                            if values:
                                values.pop(0)
                            else:
                                device_publish_status[topic] = True
                        device_ts = ts.isoformat(' ')
                        #Set time stamp  of header to actual time stamp in the data entry
                        headers = {HEADER_NAME_DATE: device_ts}
                        all_publish_message = [pt_values, meta]
                        self._publish_all_message(topic_all, headers, all_publish_message)

                    pt_values.clear()
                    meta.clear()
                else:
                    _log.debug("Data is empty: {}".format(topic))
            done = self._check_pubxxx_done(device_publish_status)
            start = end

    def _publish_all_message(self, topic_all, headers, message):
        """
        Publish "all" message on the message bus
        :param topic_all: device "all" topic
        :param headers: message header
        :param message: actual message
        :return:
        """
        # _log.debug("****************************************************************")
        # _log.debug(
        #  "ALL message for DEVICE: {0} is Headers: {1}, Message: {2}".
        #      format(topic_all,
        #             headers,
        #             message))
        # _log.debug("****************************************************************")
        self.vip.pubsub.publish(peer='pubsub',
                         topic=topic_all,
                         message=message,
                         headers=headers)
        gevent.sleep(0.2)
        _log.debug("pub done")

    def _check_pubxxx_done(self, device_publish_status):
        for topic in device_publish_status:
            if device_publish_status[topic]:
                _log.debug("Done for topic: {}".format(topic))
                return True
        return False

    def _check_pub_done(self, publish_count):
        """
        Check if publish is done
        :param publish_count:
        :return:
        """
        ln = len(publish_count.keys())
        i = 0
        for c, d in publish_count.items():
            #_log.debug("Cnt: {0}, d: {1}".format(c, d[1]))
            if d[1] == True:
                i += 1
        _log.debug("ln: {0}, i: {1}".format(ln, i))
        #if ln != 0 and ln == i:
        if i > 0:
            return True
        else: return False

    def _mongoexport_all_db(self, start, end):
        """
        Export all the device data for each device (and sub device) in individual csv files
        :param start: start time
        :param end: end time
        :return:
        """
        tids = []
        for topic in self._topics:
            ids = self._topics[topic]
            tids.extend(list(ids.keys()))
        _log.debug("Topic ids: {}".format(tids))

        args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
                self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
                self._data_collections, "--query", "", "--type", "csv", "--fields", "ts,value,topic_id",
                "--out"]

        start_time_string = start.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
        end_time_string = end.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
        query_pattern = {"$and": [{"topic_id": {"$in": tids}}, {
            "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
        _log.debug("Query pattern: {}".format(query_pattern))
        data_query_pattern = str(query_pattern)
        args[14] = data_query_pattern
        _, name = topic.rsplit('/', 1)
        args.append(name+".csv")
        p = subprocess.Popen(args)
        p.wait()

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
    """Main method."""
    try:
        args = argv[1:]
        parser = ArgumentParser(description="Play back device data from Mongo historian for given time period")

        parser.add_argument("config_file", help="Config file containing the connection info of Mongo db, "
                                                "device config path and start and end time for playback")
        parser.add_argument("topic", help="Device topic for playback")
        args = parser.parse_args(args)

        print("Arguments: {0}, {1}".format(args.config_file, args.topic))
        keystore = KeyStore()
        datapub = DataPlayback(args.config_file,args.topic, address=get_address(), identity='DATA_PLAYBACK_SIGMA1',
                                enable_store=False, publickey=keystore.public, secretkey=keystore.secret)
        event = gevent.event.Event()
        glet = gevent.spawn(datapub.core.run, event)
        event.wait(timeout=5)
        datapub.playback_data()
    except Exception as e:
        print(e)
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
