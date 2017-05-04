from datetime import datetime, timedelta
import pytz
from argparse import ArgumentParser
import sys
from csv import DictReader, DictWriter
from volttron.platform.agent import utils
import logging
import os
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)


class DataChecker:
    def __init__(self, rootdir, **kwargs):
        self._fieldnames = ['From', 'To']
        #files = os.listdir('export')
        #for name in files:
        for subdir, dirs, files in os.walk(rootdir):
            #_, filename = data_file_path.split('/', 1)
            for file in files:
                name = os.path.join(subdir, file)
                _, gap_name = subdir.split('/', 1)
                gap_name = gap_name.replace('/', '-')
                gap_name = gap_name + '-' + file
                gaps_filename = os.path.join("gaps", gap_name)
                _log.debug("file: {}".format(gaps_filename))
                with open(gaps_filename, 'w') as csvfile:
                    writer = DictWriter(csvfile, fieldnames=self._fieldnames)
                    writer.writeheader()
#                name = 'export/'+name
                self._read_csv(name, gaps_filename)

    def _read_csv(self, rdfile, wtfile):
        # _log.debug("Registry: {}".format(registry_file))
        rows = []
        prev_ts = None
        curr_ts = None
        gap_ts = None
        try:
            with open(rdfile) as f:
                for row in DictReader(f):
                    curr_ts = row['ts']
                    curr_ts = datetime.strptime(
                        curr_ts[:-1],
                        '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=pytz.utc)

                    if prev_ts:
                        threshold_ts = prev_ts + timedelta(minutes=60)

                        if curr_ts >= threshold_ts:
                            _log.debug("prev ts: {0}, curr_ts Time: {1}, threshold Time: {2}".format(prev_ts, curr_ts, threshold_ts))
                            #save gap
                            self._write_csv(wtfile, prev_ts, curr_ts)
                    prev_ts = curr_ts
                    #_log.debug("Prev Time: {0}, Curr Time: {1}".format(prev_ts, curr_ts))
        except IOError as ex:
            _log.debug("File error: {}".format(ex))
            return []
        return rows

    def _write_csv(self, file, from_ts, to_ts):
        newrow = dict()
        with open(file, 'a') as csvfile:
            writer = DictWriter(csvfile, fieldnames=self._fieldnames)
            from_string = ''
            to_string = ''
            try:
                from_string = from_ts.strftime('%Y-%m-%dT%H:%M:%S.%f')
                to_string = to_ts.strftime('%Y-%m-%dT%H:%M:%S.%f')
                newrow['From'] = from_string
                newrow['To'] = to_string
            except KeyError:
                _log.debug("Write priority key error")

            writer.writerow(newrow)

def main(argv=sys.argv):
    """Main method."""
    try:
        args = argv[1:]
        parser = ArgumentParser(description="Check for data gaps")

        parser.add_argument("root_dir", help="Root directory containing all CSV files exported from mongo")
        args = parser.parse_args(args)
        print("Arguments: {0}".format(args.root_dir))
        data_checker = DataChecker(args.root_dir)
    except Exception as e:
        print(e)
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass