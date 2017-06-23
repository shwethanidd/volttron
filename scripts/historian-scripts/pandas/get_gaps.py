import sys
import json
import pandas as pd
import os
import glob
import pytz
from datetime import datetime, timedelta
from csv import DictReader, DictWriter

def get_topicids(topics_file):
    topicid_map = dict()
    topic_map = dict()
    str_map = dict()
    with open(topics_file, 'rb') as topicsfile:
        for row in topicsfile:
            data = json.loads(row)
            topic = data['topic_name']
            id = data['_id']['$oid']
            topicid_map[str(topic)] = data['_id']
            topic_map[id] = topic
            str_map[str(id)] = topic
    return topicid_map, str_map, topic_map

#rootdir = bsf_csf
def read_gaps_files(rootdir):
    prod_topics, prod_strmap, prod_topicmap = get_topicids('prod_topics.json')
    anon_topics, anon_strmap, anon_topicmap = get_topicids('anon_topics.json')
    ts = []

    import_path = 'import'
    if not os.path.exists(import_path):
        os.makedirs(import_path)

    not_found_path = 'not_found'
    if not os.path.exists(not_found_path):
        os.makedirs(not_found_path)

    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            name = file[:-4]
            name = os.path.join(subdir, name)
            _, name = name.split('/', 1)
#            print name
# 	    print anon_topics
            try:
                a_oid = anon_topics[str(name)]
                anon_oid = a_oid['$oid']
#                print anon_oid
		rep_name = name.replace('BUILDING4', 'BSF_CSF')
                prod_oid = prod_topics[rep_name]['$oid']
#                print prod_oid
                p_name = 'prod_historian-' + prod_oid + '.csv'
                prod_file = os.path.join('work', p_name)
                del ts[:]
                if not os.path.exists(prod_file):
                    with open('not_found/id.txt', 'a') as f:
                        f.write("{}\n".format(prod_oid))
                        f.close()
                else:
                    fromto = tuple()
                    with open(os.path.join(subdir, file)) as f:
                        for row in DictReader(f):
                            ts.append((row['From'], row['To']))

                    # Read prod file
                    df2 = pd.read_csv(prod_file, index_col=None)
                    try:
                        df2['ts'] = pd.to_datetime(df2['ts'], format='%Y-%m-%d %H:%M:%S.%f', exact=True)
                    except ValueError:
                        print("Wrong ts format {}".format(prod_oid))
                        pass
                    try:
                        del df2['topic_id']
                    except KeyError:
                        pass
                    df2.sort(['ts'], ascending=True, inplace=True)
                    nm = 'historian_anon-' + anon_oid + '.csv'
                    import_file = import_path+'/'+nm
                    gap = pd.DataFrame()
                    gp = pd.DataFrame()
                    with open(import_file, 'w') as f:
                        writer = DictWriter(f, fieldnames=['ts', 'value'])
                        writer.writeheader()

                        for fromto in ts:
                            try:
                                start = datetime.strptime(
                                fromto[0],
                                '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc)
                                end = datetime.strptime(
                                fromto[1],
                                '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc)

                                start = start + timedelta(seconds=30)
                                end = end - timedelta(seconds=30)

                                gap = df2[(df2['ts'] > start) & (df2['ts'] < end)]
                            except TypeError as exc:
                                print("TypeError in {}".format(exc))
                                pass

                            try:
                                gp['ts'] = gap['ts'].map(lambda x: string_to_date(x))
                                gp.to_csv(f, mode='a', header=False, index=False)
                            except TypeError:
                                gap.to_csv(f, mode='a', header=False, index=False)

            except KeyError as exc:
                print("Anon Topicid not found {}".format(exc))

    print("All Done")


def string_to_date(x):
    try:
        temp = datetime.strptime(
            x,
            '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc)
    except TypeError:
        raise
    except ValueError:
        x += '.000'
        print x
    return x

def main():
    print("In main")
    read_gaps_files("gaps_final")

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
