import sys
import json
import os
from csv import DictReader, DictWriter
import subprocess
import shutil
from time import sleep

def get_topicids(topics_file):
    topicids = []
    topic_map = dict()
    with open('topics.json', 'rb') as topicsfile:
        for row in topicsfile:
            data = json.loads(row)
            topic = data['topic_name']
            id = data['_id']['$oid']
            topicids.append(id)
            topic_map[topic] = id
    return topicids, topic_map


def read_gaps_files(path, rootdir):
    prod_topicids, prod_topicmap = get_topicids('prod_topics.json')
    anon_topicids, anon_topicmap = get_topicids('anon_topics.json')
    ts = []
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            name = os.path.join(subdir, file)
            ts.clear()
            #Read one line at a time
            ts = read_csv(name)
            #topicid map
            topicids = []
            if id in anon_topicids:
                anon_topic = anon_topicmap[id]
                prod_topic = anon_topic.replace("BUILDING4", "BSF_CSF")

                try:
                    prod_topicid = prod_topicmap[prod_topic]
                    export_mongo_to_csv(prod_topicid, ts)
                except KeyError as exc:
                    print("Topicid not found".format(exc))

def read_csv(rdfile):
    ts = []
    try:
        with open(rdfile) as f:
            for row in DictReader(f):
                ts.append((row['From'], row['To']))
    except IOError:
        pass
        return ts
    return ts

def export_mongo_to_csv(topicid, ts):
    ps = []

    i = 0
    count = len(ts)
    print("Number of Timestamps to export {}".format(len(ts)))
    while len(ts) > 0:
        start, end = ts.pop()
        p, file = export_data(topicid,start, end)
        item = dict(process=p, filename=file)
        ps.append(item)
        sleep(2)

    for item in ps:
        p = item['process']
        f = item['filename']
        p.wait()
        print("Done with export {}, {} to export".format(i, count - i))

        _, original_exported_file = f.split('/', 1)
        new_exported_file = os.path.join("gaps_fill", original_exported_file)
        # new_exported_file = "completed/" + original_exported_file
        path, file = new_exported_file.rsplit('/', 1)
        if not os.path.exists(path):
            os.makedirs(path)
        shutil.move(f, new_exported_file)
        print("Moved {}".format(f))

    print("All Done")


def export_data(self, topicid, start, end):
    args = ["mongoexport", "--host", self._hosts, "--db", self._db_name, "--authenticationDatabase",
            self._authsource, "--username", self._user, "--password", self._passwd, "--collection",
            "data", "--query", "", "--type", "csv", "--fields", "ts,value,topic_id",
            "--sort", "{ts: 1}", "--out", ""]

    print("Running Query for Data Table")
    data_collection = 'data'
    start_time_string = start.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
    end_time_string = end.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'

    query_pattern = {"$and": [{"topic_id": {"$in": topicid}}, {
        "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}

    # query_pattern = {"topic_id": topicid}
    args[14] = str(query_pattern)

    # print("query: {}".format(args))
    filename = self._db_name + "-" + topicid['$oid']
    outfile = "gaps_fill/{}.csv".format(filename)
    args[22] = outfile
    stdout = "log/{}.log".format(filename)
    stderr = "log/{}.err".format(filename)
    return subprocess.Popen(args, stdout=open(stdout, 'w'), stderr=open(stderr, 'w')), outfile

def main():
    read_gaps_files()


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass