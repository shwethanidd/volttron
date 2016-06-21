
class PubSubCy(object):
    def __init__(self):
        #[bus][prefix][peers]
        self._cy_peer_subscriptions = {}
        #[peer][bus][prefix][callbacks]
        self._cy_subscriptions = {}

    #Subscriber
    def cy_subscribe(self, char* peer, char* prefix, callback, char* bus=''):
        self.cy_add_subscriptions(peer, prefix, callback, bus)
        self.cy_add_peer_subscriptions(peer, prefix, bus)

    #At local subscriber
    def cy_add_subscriptions(self, char* peer, char* prefix, callback, char* bus):
        #Find buses for given peer
        print("cy_add_subscriptions {0}, {1}, {2}".format(peer, prefix, bus))
        try:
            buses = self._cy_subscriptions[peer]
        except KeyError:
            print("A")
            self._cy_subscriptions[peer] = buses = {}
        #Find subscriptions for given peer, bus
        try:
            subscriptions = buses[bus]
        except KeyError:
            print("B")
            buses[bus] = subscriptions = {}
        #Find the callbacks set for given prefix
        try:
            callbacks = subscriptions[prefix]
        except KeyError:
            print("C")
            subscriptions[prefix] = callbacks = set()
        callbacks.add(callback)
        print("Added subscription: {}".format(self._cy_subscriptions))

    #At peer, who is publishing
    def cy_add_peer_subscriptions(self, char* peer, char* bus, char* prefix):
        #Find subscriptions (another dictionary of prefix, peer) for given bus
        try:
            subscriptions = self._cy_peer_subscriptions[bus]
        except KeyError:
            self._cy_peer_subscriptions[bus] = subscriptions = {}
        try:
            subscribers = subscriptions[prefix]
        except KeyError:
            subscriptions[prefix] = subscribers = set()
        subscribers.add(peer)

    def distribute(self, char* peer, char* topic, headers, message=None, char* bus=''):
        cdef char* prefix
        #print("Distribute {0}, {1}, {2}".format(peer, topic, bus))
        try:
            subscriptions = self._cy_peer_subscriptions[bus]
        except KeyError:
            print("Still key error")
            self._cy_peer_subscriptions[bus] = subscriptions = {}
        subscribers = set()
        print("Subscription items {}".format(subscriptions))
        for prefix, subscription in subscriptions.iteritems():
            #print("Prefix: {0}, Topic: {1}".format(prefix, topic))
            if subscription and self.cy_is_prefix_in_topic(prefix, topic):
                subscribers |= subscription

        return subscribers

    #Publisher
    def cy_publish(self, object topic, object header, object message, char* bus=''):
        #fill the header and pass to distribute
        self.distribute('pubsub', header, topic, message, bus='')

    #At subscriber
    def cy_distribute(self, char* peer, object header, object topic, object message, char* bus=''):
        self.cy_peer_push(peer, header, topic, message)

    #At subscriber
    def cy_peer_push(self, char* peer, char* sender, char* topic, object headers=None, object message=None, char* bus=''):
        #Extract callback from _my_subscription
        subscriptions = self._cy_subscriptions[peer][bus]
        for prefix, callbacks in subscriptions.iteritems():
            if self.cy_is_prefix_in_topic(prefix, topic):
                for callback in callbacks:
                    callback(peer, sender, bus, topic, headers, message)

    def cy_is_prefix_in_topic(self, prefix, topic):
        return topic[:len(prefix)] == prefix or prefix == ''
