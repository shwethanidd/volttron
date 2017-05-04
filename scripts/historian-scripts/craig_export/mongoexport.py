import subprocess
import pymongo
import os
import sys
from time import sleep

client = pymongo.MongoClient("mongodb://reader:volttronReader@vc-db.pnl.gov/prod_historian")
db = client.get_default_database()
print(db.topics.count())
processes = []

topics = list(db.topics.find())

def touch(fname):
    try:
        os.utime(fname, None)
    except OSError:
        open(fname, 'a').close()

def export_func(topicid, database):
    outfile="export/"+database+"-"+str(topicid) + ".csv"
    print outfile
    query= {"topic_id": topicid}
    print query
    query_pattern = str(query)

    args = ["mongoexport", "--host", "vc-db.pnl.gov", "--db", "prod_historian", "--authenticationDatabase",
            "prod_historian", "--username", "reader", "--password", "volttronReader", "--collection",
            "data", "--query", query_pattern, "--type", "csv", "--fields", "tcd opic_id,ts,value", "--out", outfile]
    return args

def start_process(topicid, database):
    #args = ['./export.sh', str(topicid), database]
    stdout = "log/{}-{}.log".format(str(topicid), database)
    stderr = "log/{}-{}.err".format(str(topicid), database)
    export_file = 'export/' + database + str(topicid) + ".csv"
    touch(export_file)
    args = export_func(topicid, database)
    return subprocess.Popen(args, stdout=open(stdout, 'w'), stderr=open(stderr, 'w'))

database_read = sys.argv[1]
max_processes = 10
while len(topics) > 0:
    topic = topics.pop()
    print("processing: {} {}".format(str(topic['_id']), topic['topic_name']))
    done_file = "done/{}-{}.csv".format(database_read, str(topic['_id']))
    if os.path.exists(done_file):
        print("already processed: {}".format(topic['_id']))
        continue
    processes.append((done_file, start_process(topic['_id'], database_read)))

    while len(processes) > max_processes:
        new_processes = []
        for df, p in processes:
            results = p.poll()
            if results is None:
                new_processes.append((df, p))
            else:
                print("completed: {}".format(df))
                touch(df)
        processes = new_processes
        sleep(5)

while len(processes) > 0:
    new_processes = []
    for df, p in processes:
        results = p.poll()

        if results is None:
            new_processes.append((df, p))
        else:
            print("completed: {}".format(df))
            touch(df)
    processes = new_processes
    sleep(5)
