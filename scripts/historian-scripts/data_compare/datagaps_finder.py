import sys
import logging
from csv import DictReader, DictWriter
from argparse import ArgumentParser
from volttron.platform.agent.utils import parse_json_config
import subprocess

utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)

class DataGap_Finder:
    def __init__(self, file1, file2):
        self.mongodbclient = None

    def compare(self, file1, file2):
        rows1 = self._read_csv(file1)
        rows2 = self._read_csv(file2)
        for row in rows1:

    def _read_csv(self, file):
        # _log.debug("Registry: {}".format(registry_file))
        rows = []
        try:
            with open(file) as f:
                rows = [x for x in DictReader(f)]
        except IOError as ex:
            # _log.debug("File error: {}".format(ex))
            return []
        return rows
























#python accumulate_points.py ROB_MATH /home/volttron/volttron/config/rob_math-building-pnnl/
def main(argv=sys.argv):
    args = argv[1:]
    parser = ArgumentParser(description="Read all the points in numerous device registry csv files into a single csv file for a building")
    parser.add_argument("file1", help="actual")
    parser.add_argument("file2", help="anon")
    args = parser.parse_args(args)
    #print("Arguments: {0}, {1}".format(args.building, args.master_config_path))
    finder = DataGap_Finder(args.file, args.file2)
    finder.accumulate()

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())