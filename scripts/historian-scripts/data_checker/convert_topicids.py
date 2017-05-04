import sys
from csv import DictReader, DictWriter
from argparse import ArgumentParser
import json
import pytz
from datetime import datetime, timedelta

import os

class TopicIdsConvertor:
    def __init__(self):
        self._fieldnames = ['Timestamp', 'value', 'unit']

    def convert(self, src_path, dest_path):
        topic_id_map = {}
        meta_id_map = {}
        #topic_id_map = self._read_topics_json('topics.json')
        self._read_meta_json('meta01.json', meta_id_map)

        dest_path = dest_path + '/completed'
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        for id, name in topic_id_map.items():
            src_file = src_path + "/historian_anon-{}.csv".format(id)
            if os.path.exists(src_file):
                rows = self._read_csv(src_file)
                _, f = src_file.rsplit('/', 1)
                dest_file = dest_path + "/{}".format(f)
		        print("Writing to: ", dest_file)
                self._write_csv(dest_file, rows, meta_id_map)
            else:
                print("File not found: {}".format(src_file))

    def _read_topics_json(self, topics_file):
        topic_id_map = {}
        with open(topics_file, 'rb') as topicsfile:
            for row in topicsfile:
                data = json.loads(row)
                #print data
                id = data['_id']['$oid']
                topic_id_map[id] = data['topic_name']
        return topic_id_map

    def _read_meta_json(self, meta_file):
        meta_id_map = {}
        with open(meta_file, 'rb') as meta_file:
            for row in meta_file:
                data = json.loads(row)
                #print data
                id = data['_id']['$oid']
                meta_id_map[id] = data['units']
        return meta_id_map

    def _read_csv(self, src_file):
        rows = []
        try:
            with open(src_file, ) as f:
                rows = [x for x in DictReader(f)]
        except IOError as ex:
            #_log.debug("File error: {}".format(ex))
            return []
        return rows

    def _write_csv(self, new_file, rows, meta_id_map):
        newrow = dict()
        try:
            with open(new_file, 'a') as csvfile:
                writer = DictWriter(csvfile, fieldnames=self._fieldnames)
                for row in rows:
                    #print row
                    utc_ts = row['ts']
                    newrow['Timestamp'] = row['ts']
                    newrow['value'] = row['value']
                    tid = row['topic_id']
                    tid = tid[9:-1]
                    units = meta_id_map[tid]
                    newrow['units'] = units
                    writer.writerow(newrow)
        except KeyError:
            pass


def main(argv=sys.argv):
    args = argv[1:]
    parser = ArgumentParser(description="Convert topic ids to topic names in all files in path")
    parser.add_argument("source_path", help="Source path")
    parser.add_argument("destination_path", help="Destination path")
    args = parser.parse_args(args)
    #print("Arguments: {0}, {1}".format(args.building, args.master_config_path))
    timestp = TopicIdsConvertor()
    timestp.convert(args.source_path, args.destination_path)

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())

