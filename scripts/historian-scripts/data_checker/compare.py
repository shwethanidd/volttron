from datetime import datetime, timedelta
import pytz
from argparse import ArgumentParser
import sys
from csv import DictReader, DictWriter
from volttron.platform.agent import utils
import logging
from collections import namedtuple
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)


class DataCompare:
    def __init__(self, topic, real_data_csv, anon_data_csv, **kwargs):
        self._fieldnames = ['Topic', 'From', 'To', 'Actual', 'Anon']
        with open('comparison.csv', 'w') as csvfile:
            writer = DictWriter(csvfile, fieldnames=self._fieldnames)
            writer.writeheader()
        seb_rows = self._read_csv(real_data_csv)
        anon_rows = self._read_csv(anon_data_csv)
        done = False
        i=0
        while len(seb_rows) > 0 or done:
            seb_row = seb_row.pop()
            anon_row = anon_rows.pop()
            start_ts = seb_row[i]['From']
            anon_start_ts = anon_row[i]['From']
            end_ts = seb_row[i]['To']
            anon_end_ts = anon_row[i]['To']
            #check for overlap
            overlap = self._check_overlap(start_ts, end_ts, anon_start_ts, anon_end_ts)A
            i += 1

    def _check_overlap(self, start1, end1, start2, end2):
        overlap = 0
        latest_start = max(start1, start2)
        earliest_end = min(end1, end2)
        overlap = (earliest_end - latest_start)
        return overlap

    def _read_csv(self, registry_file):
        #_log.debug("Registry: {}".format(registry_file))
        rows = []
        try:
            with open(registry_file) as f:
                rows = [x for x in DictReader(f)]
        except IOError as ex:
            return []
        return rows

    def _write_csv(self, from_ts, to_ts, real_stats, anon_stats):
        newrow = dict()
        with open('gaps.csv', 'a') as csvfile:
            writer = DictWriter(csvfile, fieldnames=self._fieldnames)
            from_string = ''
            to_string = ''
            try:
                newrow['From'] = from_ts
                newrow['To'] = to_ts
                newrow['Actual'] = real_stats
                newrow['Anon'] = anon_stats
            except KeyError:
                _log.debug("Write key error")
            writer.writerow(newrow)

def main(argv=sys.argv):
    """Main method."""
    try:
        args = argv[1:]
        parser = ArgumentParser(description="Check for data gaps")

        parser.add_argument("data_file", help="CSV file that contains data exported from mongo")
        args = parser.parse_args(args)
        print("Arguments: {0}".format(args.data_file))
        data_checker = DataCompare(args.data_file)
    except Exception as e:
        print(e)
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass