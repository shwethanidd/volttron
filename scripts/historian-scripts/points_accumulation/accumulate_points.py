import fnmatch
import sys
from argparse import ArgumentParser
import os
from volttron.platform.agent import utils
from csv import DictReader, DictWriter
from StringIO import StringIO
from volttron.platform.messaging import topics

import logging
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)

class DataPoints_Accumulator:
    def __init__(self, building, master_config_path):
        self._master_config_path = master_config_path
        self._config_files = []
        self._fieldnames = ['Volttron Point Name', 'Units', 'Unit Details', 'BACnet Object Type',
                      'Property', 'Writable', 'Write Priority', 'Index', 'Notes']
        self._building_file = building + "_points.csv"
        with open(self._building_file, 'w') as csvfile:
            writer = DictWriter(csvfile, fieldnames=self._fieldnames)
            writer.writeheader()

    def accumulate(self):
        master_config_file = os.path.join(self._master_config_path, "master-driver.config")
        config = utils.load_config(master_config_file)
        self._config_files = config['driver_config_list']
        #_log.debug("config files: {}".format(self._config_files))
        for f in self._config_files:
            try:
                #_log.debug("Reading config file {}".format(f))
                #Get config
                device_config = utils.load_config(f)
                campus = device_config['campus']
                building = device_config['building']
                unit = device_config.get('unit', '')
                path = device_config.get('path', '')
                registry_config = device_config['registry_config']
                device = topics.DEVICES_VALUE(campus=campus,
                                                    building=building,
                                                    unit=unit,
                                                    path=path,
                                                    point='')
                _, device = device.split('/', 1)
                device = device + '/'

                #_log.debug("Device: {0}, Registry: {1}".format(device, registry_config))
                rows = self._read_csv(registry_config)
                if rows:
                    self._write_csv(device, rows)
            except ValueError:
                pass
            except KeyError:
                pass

    def _read_csv(self, registry_file):
        #_log.debug("Registry: {}".format(registry_file))
        rows = []
        try:
            with open(registry_file) as f:
                rows = [x for x in DictReader(f)]
        except IOError as ex:
            _log.debug("File error: {}".format(ex))
            return []
        return rows

    def _write_csv(self, device, rows):
        newrow = dict()
        with open(self._building_file, 'a') as csvfile:
            writer = DictWriter(csvfile, fieldnames=self._fieldnames)
            for row in rows:
                try:
                    # Skip lines that have no address yet.
                    if not row['Reference Point Name']:
                        continue
                    ref_point_name = row['Reference Point Name']
                except KeyError:
                    # Skip lines that have no address yet.
                    if not row['Point Name']:
                        continue
                    ref_point_name = row['Point Name']
                try:
                    newrow['Write Priority'] = row['Write Priority']
                except KeyError:
                    #_log.debug("Write priority key error")
                    newrow['Write Priority'] = ''

                point_name = row['Volttron Point Name']
                row['Volttron Point Name'] = device + point_name
                newrow['Volttron Point Name'] = row['Volttron Point Name']
                newrow['Units'] = row['Units']
                newrow['Unit Details'] = row['Unit Details']
                newrow['BACnet Object Type'] = row['BACnet Object Type']
                newrow['Property'] = row['Property']
                newrow['Writable'] = row['Writable']
                newrow['Index'] = row['Index']
                newrow['Notes'] = row.get('Notes', '')
                writer.writerow(newrow)

#python accumulate_points.py ROB_MATH /home/volttron/volttron/config/rob_math-building-pnnl/
def main(argv=sys.argv):
    args = argv[1:]
    parser = ArgumentParser(description="Read all the points in numerous device registry csv files into a single csv file for a building")
    parser.add_argument("building", help="Building name")
    parser.add_argument("master_config_path", help="Path for master config file")
    args = parser.parse_args(args)
    #print("Arguments: {0}, {1}".format(args.building, args.master_config_path))
    points_accumulator = DataPoints_Accumulator(args.building, args.master_config_path)
    points_accumulator.accumulate()

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())