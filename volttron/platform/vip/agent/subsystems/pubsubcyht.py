
cdef:
    struct hEntry:
        char* key
        void* data
        bint active

    struct htable:
        hEntry* table
        long size, count

    struct buses:
        htable* subscriptions

    struct peers:
        htable* bu

    peers _my_subscriptions

_my_subscriptions.bu = hm_create(5)

cdef htable* hm_create(int startsize):
    cdef htable* hm

    hm = <htable*>malloc(sizeof(htable))
    hm.table = <hEntry*>calloc(sizeof(hEntry), startsize)
    hm.size = startsize
    hm.count = 0;
    return hm

cdef htable_add(htable* hash, const void* data, char* key):
    cdef long index, step
    cdef int i
    cdef bint found = True

    if(hash.count == 0):
        hash.table[0].data = data
        hash.table[0].key = key;
        hash.table[0].active = True
        hash.count += 1
        if debug: print("hash.count: {}".format(hash.count))
        return

    if hash.count < hash.size:
        i = 0
        for i in range(hash.count):
            if (hash.table[i].active == True):
                if (hash.table[i].key[0] == key[0]):
                    if debug: print("key: {}".format(hash.table[i].key))
                    hash.table[i].data = data
                    break
            else:
                if debug: print("xxx")
                hash.table[i].data = data
                hash.table[i].key = key;
                hash.table[i].active = True
                hash.count += 1
                break
        if debug: print("reached end of count {}".format(i))
        hash.table[i+1].data = data
        hash.table[i+1].key = key;
        hash.table[i+1].active = True
        hash.count += 1

cdef void* htable_remove(htable* hash, char* key):
    cdef long index, i, step

    if hash.count < hash.size:
        for i in range(hash.count):
            if (hash.table[i].key[0] == key[0]) & (hash.table[i].active == True):
                hash.count -= 1
                break

cdef void* htable_get(htable* hash, char* key):
    cdef long index, step
    cdef int i
    if hash.count == 0: return NULL

    if debug: print("htable_get {}".format(key))
    if hash.count < hash.size:
        i = 0
        for i in range(hash.count):
            #hkey = hash.table[i].key[0]
            #k = key[0]
            if (hash.table[i].key[0] == key[0]):
                #if((hash.table[i].active == True)):
                if debug: print("Found {}".format(key))
                return hash.table[i].data
            else:
                print("key {}".format(hash.table[i].key))
                if debug: print("Active flag {}".format(hash.table[i].active))

    if debug: print("Returing NULL")
    return NULL

class PubSubCy(object):
    cdef add_my_subscriptions(char* peer, char* prefix, object callback, char* bus):
    cdef htable* bs
    cdef htable* sub
    cdef peers p
    cdef object cb
    cdef htable* fd
    #Find buses for given peer
    print("here 1")
    if(htable_get(_my_subscriptions.bu, peer) is not NULL):
        if debug: print("here 2")
        bs = <htable*>htable_get(_my_subscriptions.bu, peer)
    else:
        if debug: print("here 3")
        bs = hm_create(5)
        htable_add(_my_subscriptions.bu, bs, peer)
        if debug: print("trying get after adding {}".format(peer))
        bs = <htable*> htable_get(_my_subscriptions.bu, peer)
    if(htable_get(bs, bus) is not NULL):
        if debug: print("here 4")
        sub = <htable*>htable_get(bs, bus)
    else:
        if debug: print("here 5")
        sub = hm_create(5)
        htable_add(bs, sub, bus)
        if debug: print("trying get after adding bus")
        sub = <htable*> htable_get(bs, bus)

    if(htable_get(sub, prefix) is not NULL):
        if debug: print("here 6")
        cb = <object>htable_get(sub, prefix)
        cb = callback
    else:
        if debug: print("here 7")
        htable_add(sub, <const void*>callback, prefix)
        if debug: print("trying get after adding prefix")
        cb = <object>htable_get(sub, prefix)

#At local subscriber
# cdef add_my_subscriptions(char *peer, char *prefix, object callback, char* bus):
#     #Find buses for given peer
#     try:
#         buses = _my_subscriptions[peer]
#     except KeyError:
#         _my_subscriptions[peer] = buses = {}
#     #Find subscriptions for given peer, bus
#     try:
#         subscriptions = buses[bus]
#     except KeyError:
#         buses[bus] = subscriptions = {}
#     #Find the callbacks set for given prefix
#     try:
#         callbacks = subscriptions[prefix]
#     except KeyError:
#         subscriptions[prefix] = callbacks = set()
#     callbacks.add(callback)

#At peer, who is publishing
cdef add_peer_subscriptions(char* peer, char* prefix, char* bus):
    #Find subscriptions (another dictionary of prefix, peer) for given bus
    try:
        subscriptions = _my_peer_subscriptions[bus]
    except KeyError:
        _my_peer_subscriptions[bus] = subscriptions = {}
    try:
        subscribers = subscriptions[prefix]
    except KeyError:
        subscriptions[prefix] = subscribers = set()
    subscribers.add(peer)

#Publisher
def publish(char* peer, header=None, topic=None, message=None, bus=''):
    #fill the header and pass to distribute
    if header is None:
        header = {}
    else:
        if debug: print "Im here"
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
    distribute(peer, header, topic, message, bus=bus)

#At subscriber
cdef distribute(char* peer, object header, char* topic, object message, char* bus):
    peer_push(peer, header, topic, message, bus)

#At subscriber
cdef peer_push(char* peer, object header, char* topic, object message, char* bus):
    cdef htable* bs
    cdef htable* sub
    cdef object cb

    if(htable_get(_my_subscriptions.bu, peer) is not NULL):
        if debug: print("here 22")
        bs = <htable*>htable_get(_my_subscriptions.bu, peer)
        if(htable_get(bs, bus) is not NULL):
            if debug: print("here 42")
            sub = <htable*>htable_get(bs, bus)
            if(htable_get(sub, topic) is not NULL):
                if debug: print("here 62")
                cb = <object>htable_get(sub, topic)
                cb(header, topic, message)
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
