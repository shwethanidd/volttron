import sys
import json
import os
from csv import DictReader, DictWriter
import subprocess
import shutil
from time import sleep


def get_topicids(topics_file):
    topicid_map = dict()
    topic_map = dict()
    str_map = dict()
    with open(topics_file, 'rb') as topicsfile:
        for row in topicsfile:
            data = json.loads(row)
            topic = data['topic_name']
            id = data['_id']['$oid']
            topicid_map[topic] = data['_id']
            topic_map[id] = topic
            str_map[str(id)] = topic
    return topicid_map, str_map, topic_map


def read_gaps_files(rootdir):
    prod_topics, prod_strmap, prod_topicmap = get_topicids('prod_topics.json')
    anon_topics, anon_strmap, anon_topicmap = get_topicids('anon_topics.json')
    ts = []
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            name = os.path.join(subdir, file)
            ts = ts[:]
            # Read one line at a time
            ts = read_csv(name)
            # topicid map
            topicids = []
            f = name[:-4]
            _, oid = f.rsplit('-', 1)

            try:
                topic = anon_strmap[oid]
                # anon_topic = anon_topicmap[id]
                prod_topic = topic.replace("BUILDING4", "BSF_CSF")
                try:
                    prod_topicid = prod_topics[prod_topic]
                    export_mongo_to_csv(prod_topicid, ts)
                except KeyError as exc:
                    print("Topicid not found".format(exc))
            except KeyError as exc:
                print("Anon topic id not found".format(exc))
    print("All Done")


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
    p = ''
    f = ''
    print("Number of Timestamps to export {}".format(len(ts)))
    while len(ts) > 0:
        start, end = ts.pop()
        print start, end
        p, file = export_data(topicid['$oid'], start, end)
        item = dict(process=p, filename=file)
        ps.append(item)
        sleep(2)

    for item in ps:
        p = item['process']
        f = item['filename']

        i += 1
        p.wait()
        print("Done with export {}, {} to export".format(i, count - i))

    #        _, original_exported_file = f.split('/', 1)
    #        new_exported_file = os.path.join("gaps_fill", original_exported_file)
    # new_exported_file = "completed/" + original_exported_file


#        path, file = new_exported_file.rsplit('/', 1)
#        if not os.path.exists(path):
#            os.makedirs(path)
#        shutil.move(f, new_exported_file)
#        print("Moved {}".format(f))


def export_data(topicid, start, end):
    args = ["mongoexport", "--host", "vc-db.pnl.gov", "--db", "prod_historian", "--authenticationDatabase",
            "prod_historian", "--username", "reader", "--password", "volttronReader", "--collection",
            "data", "--query", "", "--type", "csv", "--fields", "ts,value,topic_id",
            "--sort", "{ts: 1}", "--out", ""]

    # print("Running Query for Data Table")
    data_collection = 'data'
    start_time_string = start[:-3] + 'Z'
    end_time_string = end[:-3] + 'Z'

    tid = {}
    tid['$oid'] = str(topicid)
    query_pattern = {"$and": [{"topic_id": tid}, {
        "ts": {"$gte": {"$date": start_time_string}, "$lt": {"$date": end_time_string}}}]}
    #    query_pattern = {"topic_id": topicid}
    #    print("Query pattern: {}".format(query_pattern))
    args[14] = str(query_pattern)

    # print("query: {}".format(args))
    filename = "prod_historian-" + start
    outfile = "gaps_fill/{}/{}.csv".format(tid['$oid'], filename)
    args[22] = outfile
    stdout = "log/{}.log".format(filename)
    stderr = "log/{}.err".format(filename)
    return subprocess.Popen(args, stdout=open(stdout, 'w'), stderr=open(stderr, 'w')), outfile


def main():
    read_gaps_files('gaps')


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
