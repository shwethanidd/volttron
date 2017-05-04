from csv import DictReader, DictWriter
import sys

def fileread():
    rows = []
    names = ['Topicids', 'Topics']
    newrow=dict()
    print 22
    with open('orp_anon.csv', 'w') as csvfile:
        print "ggg"
        writer = DictWriter(csvfile, fieldnames=names)
        writer.writeheader()

        try:
            with open('orphan_anon_ids.txt') as f:
                print 'rr'
                for row in f:
                    print row
                    id, name = row.split(',', 1)
                    newrow['Topicids'] = id
                    newrow['Topics'] = name
                    writer.writerow(newrow)

        except IOError:
            raise

def main(argv=sys.argv):
    """Main method."""
    try:
        fileread()
    except Exception as e:
        print(e)
if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
