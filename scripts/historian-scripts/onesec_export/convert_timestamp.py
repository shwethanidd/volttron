import sys
from csv import DictReader, DictWriter
from argparse import ArgumentParser
import dateutil.tz
from zmq.utils import jsonapi
import pytz
from datetime import datetime, timedelta
from bson.objectid import ObjectId

class TimestampConvertor:
    def __init__(self):
        self._fieldnames = ['ts', 'value', 'topic']

    def convert(self, src_file, dest_file):
        topic_id_map = {}
        topic_id_map = self._read_topics_json('topics.json')
        #self.read_temp(src_file)
        rows = self._read_csv(src_file)
        #print('Topic id map: {0}'.format(topic_id_map))
        self._write_csv(dest_file, rows, topic_id_map)

    def _read_topics_json(self, topics_file):
        topic_id_map = {}
        with open(topics_file, 'rb') as topicsfile:
            for row in topicsfile:
                data = jsonapi.loads(row)
                #print data
                topic_id = data['_id']['$oid']
                topic_id_map[topic_id] = data['topic_name']
        return topic_id_map

    def _read_csv(self, registry_file):
        rows = []
        try:
            with open(registry_file, ) as f:
                rows = [x for x in DictReader(f)]
        except IOError as ex:
            #_log.debug("File error: {}".format(ex))
            return []
        return rows

    def _write_csv(self, new_file, rows, topic_id_map):
        newrow = dict()
        try:
            with open(new_file, 'a') as csvfile:
                writer = DictWriter(csvfile, fieldnames=self._fieldnames)
                for row in rows:
                    #print row
                    utc_ts = row['ts']
                    #print utc_ts
                    utc_ts = datetime.strptime(
                        utc_ts[:-1],
                        '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=pytz.utc)
                    #print utc_ts
                    to_zone = dateutil.tz.gettz('US/Pacific')
                    local_ts =utc_ts.astimezone(to_zone)
                    #print('UTC time: {0}, Local: {1}'.format(utc_ts, local_ts))
                    newrow['ts'] = local_ts
                    newrow['value'] = row['value']
                    topic_id = row['topic_id']
                    tid = row['topic_id']
                    tid = tid[9:-1]
                    newrow['topic'] = topic_id_map[tid]
                    writer.writerow(newrow)
        except KeyError:
            pass
        #print topic_id_map[t]

def main(argv=sys.argv):
    args = argv[1:]
    parser = ArgumentParser(description="Convert UTC timestamp to Local timestamp")
    parser.add_argument("source_file", help="Mongo export file")
    parser.add_argument("destination_file", help="new file name")
    args = parser.parse_args(args)
    #print("Arguments: {0}, {1}".format(args.building, args.master_config_path))
    timestp = TimestampConvertor()
    timestp.convert(args.source_file, args.destination_file)

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())