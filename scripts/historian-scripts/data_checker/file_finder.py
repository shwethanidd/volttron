import sys
import json
import os
import fnmatch
from argparse import ArgumentParser
import shutil

def get_topicids(topics_file):
    topicids = []
    topic_map = dict()
    with open('topics.json', 'rb') as topicsfile:
        for row in topicsfile:
            data = json.loads(row)
            topic = data['topic_name']
            id = data['_id']['$oid']
            topicids.append(id)
            topic_map[id] = topic
    return topicids, topic_map

def find_files(path, topicids, topic_map):
    copy_files = []
    # cwd = os.getcwd()
    # print cwd

    # Your path here e.g. "C:\Program Files\text.txt"
    for name in topicids:
        #filename = cwd + '/' + 'completed' + '/' + 'historian_anon-' + name +'.csv'
        filename = path + '/' +'historian_anon-' + name + '.csv'
        print filename
        if os.path.exists(filename):
            print "File found!"
            copy_files.append(filename)
        else:
            print("File not found!", topic_map[name])
    return copy_files

def main(argv=sys.argv):
    """Main method."""
    try:
        args = argv[1:]
        parser = ArgumentParser(description="Check for data gaps")

        parser.add_argument("path", help="CSV files path")
        args = parser.parse_args(args)
        print("Arguments: {0}".format(args.path))
        topicids = []
        cp_files = []
        topicids = get_topicids('topics.json')
        cp_files = find_files(args.path, topicids)
        #rsync -r -v --progress -e ssh user@remote-system:/address/to/remote/file /home/user/
        print cp_files

        cwd = os.getcwd()
        path = os.path.join(cwd, "tocopy")
        print cwd
        if not os.path.exists(path):
            os.makedirs(path)
        for f in cp_files:
            _, nf = f.rsplit('/', 1)
            new_file = path + '/' + nf
            print new_file
            #shutil.copy(f, new_file)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass