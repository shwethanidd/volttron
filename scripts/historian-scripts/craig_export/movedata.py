import os
import pymongo
import shutil
import sys


if not len(sys.argv) == 2:
  print('invalid database specified')
  sys.exit(50)

database_name = sys.argv[1]
export_root = "/srv/mongo-export-shwetha"
export_data = "{}/exported-data".format(export_root)
export_done = "{}/done".format(export_root)

for f in os.listdir('done'):
  topic_id = f.split('-')[1][:-4]
  filename = "{}-{}.csv".format(database_name, topic_id)
  original_exported_file = os.path.join("export", filename)
  new_exported_file = os.path.join(export_data, filename)
  new_done_file = os.path.join(export_done, f)
  if not os.path.exists(original_exported_file):
    print("Missing {}".format(original_exported_file))
  else:
    shutil.move(original_exported_file, new_exported_file)
    shutil.copy(os.path.join("done", f), new_done_file)
    print("Moved {}".format(f))

print("Done")
