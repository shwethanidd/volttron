import time
import datetime

class PubSub(object):
    def __init__(self):
        #[bus][prefix][peers]
        self._my_peer_subscriptions = {}
        #[peer][bus][prefix][callbacks]
        self._my_subscriptions = {}

    #Subscriber
    def subscribe(self, peer, prefix, callback, bus=''):
        self.add_my_subscriptions(peer, prefix, callback, bus)
        self.add_peer_subscriptions(peer, prefix, bus)

    #At local subscriber
    def add_my_subscriptions(self, peer, prefix, callback, bus=''):
        #Find buses for given peer
        try:
            buses = self._my_subscriptions[peer]
        except KeyError:
            self._my_subscriptions[peer] = buses = {}
        #Find subscriptions for given peer, bus
        try:
            subscriptions = buses[bus]
        except KeyError:
            buses[bus] = subscriptions = {}
        #Find the callbacks set for given prefix
        try:
            callbacks = subscriptions[prefix]
        except KeyError:
            subscriptions[prefix] = callbacks = set()
        callbacks.add(callback)

    #At peer, who is publishing
    def add_peer_subscriptions(self, peer, prefix, bus=''):
        #Find subscriptions (another dictionary of prefix, peer) for given bus
        try:
            subscriptions = self._my_peer_subscriptions[bus]
        except KeyError:
            self._my_peer_subscriptions[bus] = subscriptions = {}
        try:
            subscribers = subscriptions[prefix]
        except KeyError:
            subscriptions[prefix] = subscribers = set()
        subscribers.add(peer)

    #Publisher
    def publish(self, header=None, topic=None, message=None, bus=''):
        #fill the header and pass to distribute
        if header is None:
            header = {}
        else:
            print "Im here"

        header['min-version'] = 1.0
        header['max-version'] = 3.5

        header['date'] = datetime.date.today()
        header['time'] = datetime.time.second
        header['from'] = "sample sender"

        # topic = []
        # topic.append("devices/test")
        # topic.append("record")
        # topic.append("logger")

        self.distribute('pubsub', header, topic, message, bus='')

    #At subscriber
    def distribute(self, peer, header=None, topic=None, message=None, bus=''):
        self.peer_push(peer, header, topic, message)

    #At subscriber
    def peer_push(self, peer, header=None, topic=None, message=None, bus=''):

        #Extract callback from _my_subscription
        subscriptions = self._my_subscriptions[peer][bus]
        for prefix, callbacks in subscriptions.iteritems():

            if self.is_prefix_in_topic(prefix, topic):
                for callback in callbacks:
                    callback(header, topic, message)

    def build_message(self):
        message = [{'OutsideAirTemperature3': 50.0, 'OutsideAirTemperature2': 50.0, 'OutsideAirTemperature1': 50.0, 'SampleBool2': True, 'EKG': 0.7431448254773941, 'SampleWritableShort1': 20, 'SampleWritableShort2': 20, 'SampleWritableShort3': 20, 'SampleWritableBool1': True, 'SampleWritableFloat1': 10.0, 'SampleWritableBool3': True, 'SampleWritableBool2': True, 'SampleLong3': 50, 'SampleLong2': 50, 'SampleWritableFloat2': 10.0, 'Heartbeat': True, 'SampleBool1': True, 'SampleLong1': 50, 'SampleBool3': True, 'SampleWritableFloat3': 10.0}, {'OutsideAirTemperature3': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'OutsideAirTemperature2': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'OutsideAirTemperature1': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool2': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'EKG': {'units': 'waveform', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort1': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort2': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort3': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool1': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat1': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool3': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool2': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong3': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong2': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat2': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}, 'Heartbeat': {'units': 'On/Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool1': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong1': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool3': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat3': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}}]
        return message


    def is_prefix_in_topic(self, prefix, topic):
        return topic[:len(prefix)] == prefix

    def my_devices_callback(self, header=None, topic=None, message=None):
        print("In my devices callback: Received {0} {1} {2}")#.format(header, topic, message))

    def my_records_callback(self, header=None, topic=None, message=None):
        print("In my records callback: Received {0} {1} {2}")#.format(header, topic, message))

    def publishtest(self):
        i = 0
        message = self.build_message()
        while (i < 100):
            print "Running publish test"
            self.publish(None, 'devices/all/bogus', message, '')
            self.publish(None, 'records/all/bogus', message, 'bus1')
            i = i + 1
