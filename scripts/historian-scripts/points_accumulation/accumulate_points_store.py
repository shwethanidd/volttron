import fnmatch
import sys
from argparse import ArgumentParser
import os
from volttron.platform.agent import utils
from csv import DictReader, DictWriter
from StringIO import StringIO
from volttron.platform.messaging import topics
from volttron.utils.persistance import PersistentDict
from zmq.utils import jsonapi
from volttron.platform.agent.utils import parse_json_config

import logging
utils.setup_logging(logging.DEBUG)
_log = logging.getLogger(__name__)

class DataPoints_Accumulator:
    def __init__(self, building, config_store_path):
        self._config_store_path = config_store_path
        self._driver_config_store = dict()
        self._config_files = []
        self._fieldnames = ['Volttron Point Name', 'Units',
                            'Unit Details', 'BACnet Object Type',
                            'Property', 'Writable', 'Write Priority',
                            'Index', 'Notes']
        self._building_file = building + "_points.csv"
        with open(self._building_file, 'a') as csvfile:
            writer = DictWriter(csvfile, fieldnames=self._fieldnames)
            writer.writeheader()

    def accumulate(self):
        for subdir, dir, files in os.walk(self._config_store_path):
            for file in files:
                store = subdir + os.sep + file
                _log.debug("file: {}".format(store))
                try:
                    self._driver_config_store = PersistentDict(filename=store, flag='c', format='json')
                except ValueError as exc:
                    _log.error("Error in config store format: {0}".format(exc))
                    return
                reg_config = dict()
                dev_cfg = dict()
                rows = []
                for device, val in self._driver_config_store.items():
                    data = val.get("data", None)
                    if data:
                        if device.startswith("devices"):
                            data = parse_json_config(data)
                            reg_config[device] = data.get("registry_config", None)
                            #_log.debug("device: {0}, Val: {1}".format(device, reg_config[device]))
                        else:
                            f = StringIO(data)
                            dev_cfg[device] = [x for x in DictReader(f)]

                for dev, cfg in reg_config.items():
                    _, cfg = cfg.split('/', 1)
                    try:
                        rows = dev_cfg[cfg[1:]]
                        #_log.debug("cfg: {0}, {1}".format(cfg[1], rows))
                        self._write_csv(dev, rows)
                    except KeyError as e:
                        _log.debug("Missing key: {}".format(e))

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
                    # _log.debug("Write priority key error")
                    newrow['Write Priority'] = ''

                volttron_pt_name = device + '/' + row['Volttron Point Name']
                #_log.debug("Point name: {}".format(volttron_pt_name))
                newrow['Volttron Point Name'] = volttron_pt_name
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
    points_accumulator = DataPoints_Accumulator(args.building, args.master_config_path)
    points_accumulator.accumulate()

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())