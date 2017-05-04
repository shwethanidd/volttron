import logging

logging.basicConfig(level=logging.WARN)
import csv
from crate import client as crate_client
from crate.client.exceptions import ProgrammingError
from crate_util import create_schema, insert_data_query, insert_topic_query
import pymongo
import os
import shutil
import sys

total_imported = 0


def import_data(schema, crate_con, datafile, topic_map, meta_map):
    global total_imported
    print("Importing crate file: {}".format(datafile))
    with open(datafile, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        dbrows = []
        topic_id = datafile.split('-')[-1][:-4]
        topic = topic_map[topic_id]
        meta = meta_map.get(topic_id, {})

        try:
            cursor = crate_con.cursor()
            cursor.execute(insert_topic_query(schema), [topic])
        except ProgrammingError as ex:
            if not ex.message.startswith('DocumentAlreadyExistsException'):
                print("TOPIC EXCEPTION {}: {}".format(topic, ex))
        finally:
            cursor.close()

        for row in reader:
            #      topic_id = row['topic_id'][9:-1]
            #      row['topic_id'] = row['topic_id'][9:-1]
            #      topic = topic_map[topic_id]
            #      meta = meta_map[row['topic_id']]

            if topic.startswith('PNNL'):
                source = 'scrape'
            elif topic.startswith('datalogger'):
                source = 'log'
            elif topic.startswith('record'):
                source = 'record'
            else:
                source = 'analysis'
            if not row['ts'] or not topic:
                print("Can't insert null topic id/ts {}".format(row))
                continue

            dbrows.append((row['ts'], topic, source, row['value'], meta))
            if len(dbrows) > 5000:
                cursor = crate_con.cursor()
                cursor.executemany(insert_data_query(schema), dbrows)
                cursor.close()
                total_imported += len(dbrows)
                print("inserted rows: {}".format(total_imported))
                dbrows = []

        if len(dbrows) > 0:
            cursor = crate_con.cursor()
            cursor.executemany(insert_data_query(schema), dbrows)
            cursor.close()
            total_imported += len(dbrows)
            print("inserted rows: {}".format(total_imported))
            dbrows = []


def get_files_by_file_size(dirname, reverse=False):
    """ Return list of file paths in directory sorted by file size """

    # Get list of files
    filepaths = []
    for basename in os.listdir(dirname):
        filename = os.path.join(dirname, basename)
        if os.path.isfile(filename):
            filepaths.append(filename)

    # Re-populate list with filename, size tuples
    for i in xrange(len(filepaths)):
        filepaths[i] = (filepaths[i], os.path.getsize(filepaths[i]))

    # Sort list by file size
    # If reverse=True sort from largest to smallest
    # If reverse=False sort from smallest to largest
    filepaths.sort(key=lambda filename: filename[1], reverse=reverse)

    # Re-populate list with just filenames
    for i in xrange(len(filepaths)):
        filepaths[i] = filepaths[i][0]

    return filepaths


mongo_client = pymongo.MongoClient("mongodb://reader:volttronReader@vc-db.pnl.gov/historian_anon")

HOST_DB = "http://vc-db.pnl.gov:4200"

if len(sys.argv) != 3:
    print("requires a from and two schema/db name")
    sys.exit(50)

from_schema = sys.argv[1]
to_schema = sys.argv[2]

db = mongo_client.get_default_database()
processes = []

topic_map = {}
meta_map = {}

for t in db.topics.find():
    topic_map[str(t['_id'])] = t['topic_name']

for meta in db.meta.find():
    meta_map[str(meta['topic_id'])] = meta['meta']

crate_con = crate_client.connect(HOST_DB)
create_schema(crate_con, to_schema)

data_root = "/srv/mongo-export-craig"
data_export = os.path.join(data_root, "exported-data")
done_crate = os.path.join(data_root, "done-crate")
done_export = os.path.join(data_root, "done")
count = 0

for f in get_files_by_file_size(data_export, True):  # os.listdir(done_export):
    f = os.path.basename(f)
    topic_id = f.split('-')[1][:-4]
    filename = "{}-{}.csv".format(from_schema, topic_id)
    data_file = os.path.join(data_export, filename)
    done_file = os.path.join(done_crate, filename)
    if not os.path.exists(data_file):
        print("Missing: {}".format(data_file))
    else:
        import_data(to_schema, crate_con, data_file, topic_map, meta_map)
        shutil.move(data_file, done_file)
# new_exported_file = os.path.join(export_data, filename)
#  new_done_file = os.path.join(export_done, f)

