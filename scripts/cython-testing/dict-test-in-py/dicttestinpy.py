
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
        header['date-time'] = "June 15"
        header['from'] = "sample sender"

        # topic = []
        # topic.append("devices/test")
        # topic.append("record")
        # topic.append("logger")

        if message is None:
            message = {}
        message['Over-Tempr'] = 5.6
        message['Current'] = 103
        message['Voltage'] = 89
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


    def is_prefix_in_topic(self, prefix, topic):
        return topic[:len(prefix)] == prefix

    def my_devices_callback(self, header=None, topic=None, message=None):
        print("In my devices callback: Received {0} {1} {2}".format(header, topic, message))

    def my_records_callback(self, header=None, topic=None, message=None):
        print("In my records callback: Received {0} {1} {2}".format(header, topic, message))


    def publishtest(self):
        i = 0
        while (i < 100):
            print "Running publish test"
            self.publish(None, 'devices/all/bogus', None, '')
            #self.publish(None, 'records/all/bogus', None, 'bus1')
            i = i + 1
