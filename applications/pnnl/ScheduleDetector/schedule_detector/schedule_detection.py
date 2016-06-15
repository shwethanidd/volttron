# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2016, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of the FreeBSD
# Project.
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization that
# has cooperated in the development of these materials, makes any
# warranty, express or implied, or assumes any legal liability or
# responsibility for the accuracy, completeness, or usefulness or any
# information, apparatus, product, software, or process disclosed, or
# represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does not
# necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
# }}}
import csv
import logging
import sys
import re
import itertools
import datetime as dt
import gevent
from dateutil.parser import parse
import numpy as np
from pandas import DataFrame as df
from scipy.stats import norm
import pylab as pl
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt

from volttron.platform.agent import utils
from volttron.platform.agent.utils import setup_logging
from volttron.platform.vip.agent import Agent, Core
from volttron.platform.messaging import (headers as headers_mod, topics)

__version__ = "0.1.0"
__author1__ = 'Woohyun Kim <woohyun.kim@pnnl.gov>'
__author2__ = 'Robert Lutes <robert.lutes@pnnl.gov>'
__copyright__ = 'Copyright (c) 2016, Battelle Memorial Institute'
__license__ = 'FreeBSD'
DATE_FORMAT = '%m-%d-%y %H:%M'

setup_logging()
_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.info,
                    format='%(asctime)s   %(levelname)-8s %(message)s',
                    datefmt=DATE_FORMAT)


def z_normalization(time_series, data_mean, std_dev):
    if np.prod(data_mean.shape) == 0  or np.prod(std_dev.shape) == 0:
        data_mean = time_series.mean(axis=0)
        std_dev = time_series.std(axis=0)
    return ((time_series - data_mean) / std_dev), data_mean, std_dev


def paa_transform(ts, n_pieces):
    splitted = np.array_split(ts, n_pieces) ## along columns as we want
    return np.asarray(map(lambda xs: xs.mean(axis=0), splitted))


def sax_transform(ts, alphabet, data_mean, std_dev):
    n_pieces = ts.size
    alphabet_sz = len(alphabet)
    thresholds = norm.ppf(np.linspace(1./alphabet_sz, 1-1./alphabet_sz, alphabet_sz-1))

    def translate(ts_values):
        return np.asarray([(alphabet[0] if ts_value < thresholds[0]
                            else (alphabet[-1]
                                  if ts_value > thresholds[-1]
                                  else alphabet[np.where(thresholds <= ts_value)[0][-1]+1]))
                           for ts_value in ts_values])
    normalized_ts, data_mean, std_dev = z_normalization(ts, data_mean, std_dev)
    paa_ts = paa_transform(normalized_ts, n_pieces)
    return np.apply_along_axis(translate, 0, paa_ts), data_mean, std_dev


def compare(s1, s2):
    for i, j in zip(s1, s2):
        if abs(ord(i) - ord(j)) >= 2:
            return abs(ord(i) - ord(j))
        else:
            return 0


def norm_area(n):
    if n == 2:
        return np.power(norm.ppf(0.25), 2)
    elif n == 3:
        return np.power(2*norm.ppf(0.25), 2)
    else:
        return


def check_run_status(timestamp_array, current_time, no_required_data):
    last_time = timestamp_array[-1].to_datetime()
    if timestamp_array.size > 0 and last_time.day != current_time.day:
        if timestamp_array.size < no_required_data:
            return None
        return True
    return False


def create_alphabet_dict(alphabet):
    alphabet_dict = {}
    alphabet_length = len(alphabet)
    for item in xrange(alphabet_length):
        if item <= (alphabet_length - 1)/2:
            alphabet_dict[alphabet[item]] = 0
        else:
            alphabet_dict[alphabet[item]] = 1
    return alphabet_dict


def compare_detected_reference(current_reference, _time, status_array):
    reference_time = [timestamp[0] for timestamp in current_reference]
    reference_status = [status[1] for status in current_reference]
    start_range = reference_time.index(_time[0])
    end_range = reference_time.index(_time[-1]) + 1
    reference_status = reference_status[start_range:end_range]
    compared_status = []
    for ind in xrange(len(status_array)):
        if status_array[ind] == reference_status[ind]:
            compared_status.append(0)
        else:
            compared_status.append(1)
    return [_time, status_array, reference_status, compared_status]
    

def create_confusion_array(detected_series, reference_series):
    occupied = [0, 0]
    unoccupied = [0, 0]
    for reference, detected in zip(reference_series, detected_series):
        if reference == 1:
            if reference == detected:
                occupied[0] += 1
            else:
                occupied[1] += 1
        else:
            if reference == detected:
                unoccupied[0] += 1
            else:
                unoccupied[1] += 1
    return np.array([occupied,unoccupied])


def create_confusion_figure(cm, file_name, title='Confusion occupancy matrix', cmap=plt.cm.Blues):
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)

    plt.colorbar()

    target_names = ['occupancy', 'unoccupancy']
    tick_marks = np.arange(len(target_names))

    plt.xticks(tick_marks, target_names)
    plt.yticks(tick_marks, target_names)

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.savefig(file_name)
    plt.close()


def sax_schedule(config_path, **kwargs):
    """Symbolic analysis of time series data to determine HVAC/building
    schedule.
    :param kwargs: Any driver specific parameters"""
    config = utils.load_config(config_path)
    agent_id = config.get('agentid', None)

    device = dict((key, config[key]) for key in ['campus', 'building', 'unit'])

    vip_destination = config.get('vip_destination', None)

    device_topic = topics.DEVICES_VALUE(campus=device.get('campus'),
                                        building=device.get('building'),
                                        unit=device.get('unit'),
                                        path='',
                                        point='all')
    _log.info('topic: {}'.format(device_topic))

    class Schedule_Detection(Agent):
        """Symbolic schedule detection.
        """

        def __init__(self, **kwargs):
            """
            Initializes agent
            :param kwargs: Any driver specific parameters"""

            super(Schedule_Detection, self).__init__(**kwargs)
            self.p_name = config.get('point_name')
            self.no_required_data = 25
            self.sample = config.get('sample_rate', '15Min')
            self.alphabet = config.get('alphabet', 'abcd')
            self.alphabet_dict = create_alphabet_dict(self.alphabet)
            self.output_directory = config.get('output_directory', './')
            self.data_mean = np.empty(0)
            self.std_dev = np.empty(0)
            def date_parse(dates):
                return [parse(timestamp).time() for timestamp in dates]

            operational_schedule = config.get('operational_schedule')
            self.reference_schedule = None
            if operational_schedule is not None:
                self.operational_schedule = {parse(key).weekday(): date_parse(value) for key, value in operational_schedule.items()}
                self.reference_schedule = self.create_reference_schedule()
            self.initialize()

        def initialize(self):
            self.data_arr = None

        def weekly_reset(self):
            self.data_mean = np.empty(0)
            self.std_dev = np.empty(0)

        @Core.receiver('onstart')
        def starup(self, sender, **kwargs):
            """
            Starts up the agent and subscribes to device topics
            based on agent configuration.
            :param sender:
            :param kwargs: Any driver specific parameters
            :type sender: str"""
            self.initialize()
            _log.info('Subscribing to: {campus}/{building}/{unit}'.format(**device))
            self.vip.pubsub.subscribe(peer='pubsub',
                                      prefix=device_topic,
                                      callback=self.new_data)

        def new_data(self, peer, sender, bus, topic, headers, message):
            """Call back method for device data subscription."""
            _log.info('Receiving new data.')
            current_time = parse(headers.get('Date'))
            check_run = False
            data = message[0]
            data_point = data[self.p_name]
            if self.data_arr is not None:
                timestamp_array = self.data_arr.index
                check_run = check_run_status(timestamp_array, current_time, self.no_required_data)
            if check_run:
                self.timeseries_to_sax()
                self.initialize()
                _log.info('Daily reinitialization.')
            self.frame_data(data_point, current_time)

        def timeseries_to_sax(self):
            """Convert time series data to symbolic form."""
            _log.info('Creating SAX from time series.')
            data_array = self.data_arr.resample(self.sample, how="mean")
            index_header = ['Time', 'Detected Status']
            sax_time = [item.time() for item in data_array.index]
            sax_data, self.data_mean, self.std_dev = sax_transform(data_array,
                                                                   self.alphabet,
                                                                   self.data_mean,
                                                                   self.std_dev)
            symbolic_array = [item[0] for item in sax_data]
            status_array = [self.alphabet_dict[symbol] for symbol in symbolic_array]
            list_output = [sax_time, status_array]
            file_name = self.output_directory + "SAX-" + str(data_array.index[0].to_datetime().date())
            if self.reference_schedule is not None:
                current_reference = self.reference_schedule[data_array.index[0].weekday()]
                list_output = compare_detected_reference(current_reference, sax_time, status_array)
                index_header = ['Time', 'Detected Status', 'Reference Schedule', 'Comparison']
                confusion_array = create_confusion_array(list_output[1], list_output[2])
                create_confusion_figure(confusion_array, file_name + ".png")

            if data_array.index[0].weekday() == 6:
                self.weekly_reset()
                _log.info('Weekly reset.')
            _log.info('Logged status: {}'.format(list_output))
            file_name =  file_name + ".csv"
            with open(file_name, 'wb') as f_handle:
                writer = csv.DictWriter(f_handle, fieldnames=index_header, delimiter=',')
                writer.writeheader()
                for val in itertools.izip_longest(*list_output):
                    wr = csv.writer(f_handle, dialect='excel')
                    wr.writerow(val)
            f_handle.close()

        def frame_data(self, data, ts):
            """
            Creates/appends dataframe for storage of time series data.
            :param data: array with one value to append to dataframe.
            :type data: array
            :param ts: timestamp for associated data
            :type datetime
            """
            _log.info('Create/append dataframe.')
            data_arr = df([data], columns=[self.p_name], index=[ts])
            if self.data_arr is None:
                self.data_arr = data_arr
                return
            self.data_arr = self.data_arr.append(data_arr)
            return

        def create_reference_schedule(self):
            match = re.match(r"([0-9]+)([a-z]+)", self.sample, re.I)
            match = match.groups()
            reference_schedule = {key: [] for key in self.operational_schedule}
            unoccupied_token = dt.time(hour=0, minute=0)
            sample_per_hour = 60/int(match[0])
            for _day, sched in self.operational_schedule.items():
                for _hours in xrange(24):
                    for _minutes in xrange(sample_per_hour):
                        current_time = dt.time(hour=_hours, minute=_minutes*int(match[0]))
                        if sched[0] == unoccupied_token and sched[1] == unoccupied_token:
                            status = 0
                        elif current_time < sched[0] or current_time > sched[1]:
                            status = 0
                        else:
                            status = 1
                        status_tuple = (current_time, status)
                        reference_schedule[_day].append(status_tuple)
            return reference_schedule

    Schedule_Detection.__name__ = 'sax_schedule'
    return Schedule_Detection(**kwargs)


def main(argv=sys.argv):
    """ Main method."""
    utils.vip_main(sax_schedule)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass

