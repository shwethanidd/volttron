import json
import pandas as pd
import os
import shutil
import sys
import time

def get_topicids(topics_file):
    topicids = []
    topic_map = dict()
    str_map = dict()
    with open(topics_file, 'rb') as topicsfile:
        for row in topicsfile:
            data = json.loads(row)
            topic = data['topic_name']
            id = data['_id']['$oid']
            topicids.append(id)
            topic_map[str(topic)] = id
            str_map[str(id)] = topic
    return topicids, str_map, topic_map

def rename(rootdir):
    anon_topic_ids, anon_str_map, anon_topic_name_map = get_topicids("anon_topics.json")
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            f = file[:-4]
            print f
            _, oid = f.rsplit('-', 1)
            topic = anon_str_map[oid]
            prefix, pt = topic.rsplit('/', 1)
            path = 'final/' + prefix
            new_file = path + '/' + pt + '.csv'
            if not os.path.exists(path):
                os.makedirs(path)

            df = pd.read_csv(subdir+'/'+file, index_col=None)
            df.rename(columns={'ts': 'Timestamp'}, inplace=True)
            df.to_csv(new_file, index=False)
            time.sleep(0.5)
            #shutil.move(f, new_file)

def main(argv=sys.argv):
    rename('merged/bsf_csf')

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())



