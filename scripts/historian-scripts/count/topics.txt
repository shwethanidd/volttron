import csv
import subprocess
import pymongo
import os
import sys
from time import sleep

if len(sys.argv) != 2:
    print("Invalid number of arguments, expecting database naem as parameter")
    sys.exit(5)

database_name = sys.argv[1]

client = pymongo.MongoClient("mongodb://reader:volttronReader@vc-db.pnl.gov/{}".format(database_name))
db = client.get_default_database()

writer = csv.DictWriter(sys.stdout, fieldnames=['id', 'topic'])

writer.writeheader()
for t in list(db.topics.find()):
  writer.writerow(dict(id=str(t['_id']), topic=str(t['topic_name'])))
#writer.close()
client.close()

