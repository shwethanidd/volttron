from libc.stdlib cimport malloc, free, calloc
from libc.string cimport strcmp, strlen
from cpython.string cimport PyString_AsString

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

    peers _cy_subscriptions
    cdef debug = False

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

    cdef void* htable_get_cb(htable* hash, char* key):
        cdef long index, step
        cdef int i
        if hash.count == 0: return NULL

        if debug: print("htable_get {}".format(key))
        if hash.count < hash.size:
            i = 0
            for i in range(hash.count):
                if debug: print("htable_get Key: {0}, key: {1}, data: {2}".format(key,
                    hash.table[i].key, <object>hash.table[i].data))
                if cy_is_prefix_in_topic(hash.table[i].key, key):
                    #if((hash.table[i].active == True)):
                    if debug: print("Found Key: {0}, key: {1}".format(key,
                    hash.table[i].key))
                    return hash.table[i].data
                else:
                    print("key {}".format(hash.table[i].key))
                    if debug: print("Active flag {}".format(hash.table[i].active))

        if debug: print("Returing NULL")
        return NULL

    cdef cy_is_prefix_in_topic(prefix, topic):
        return topic[:len('devices')] == 'devices'

class PubSubCy(object):
    def __init__(self):
        self._cy_peer_subscriptions = {}
        _cy_subscriptions.bu = hm_create(100)
        self._cback = set()

    def cy_add_subscriptions(self, char* peer, char* prefix, callback, char* bus=''):
        cdef htable* bs
        cdef htable* sub
        cdef peers p
        cdef object cb
        cdef htable* fd
        cdef char* prefix1 = "devices"
        self._cback.add(callback)

        #Find buses for given peer
        print("here 1")
        if(htable_get(_cy_subscriptions.bu, peer) is not NULL):
            if debug: print("here 2")
            bs = <htable*>htable_get(_cy_subscriptions.bu, peer)
        else:
            if debug: print("here 3")
            bs = hm_create(5)
            htable_add(_cy_subscriptions.bu, bs, peer)
            if debug: print("trying get after adding {}".format(peer))
            bs = <htable*> htable_get(_cy_subscriptions.bu, peer)
        if(htable_get(bs, bus) is not NULL):
            if debug: print("here 4")
            sub = <htable*>htable_get(bs, bus)
        else:
            if debug: print("here 5")
            sub = hm_create(5)
            htable_add(bs, sub, bus)
            if debug: print("trying get after adding bus")
            sub = <htable*> htable_get(bs, bus)

        if(htable_get(sub, prefix1) is not NULL):
            if debug: print("here 6 {}".format(prefix))
            cb = <object>htable_get(sub, prefix1)
            if debug: print("GOT FROM LIST CALLBACK: {0}, new callback {1}".format(cb, callback))
            #cb = callback
        else:
            if debug: print("here 7 prefix {0} {1}".format(prefix1, callback))
            htable_add(sub, <const void*>callback, prefix1)
            if debug: print("trying get after adding prefix")
            cb = <object>htable_get(sub, prefix1)
            if debug: print("CALLBACK: {0}, new callback {1}".format(cb, callback))

    #At peer, who is publishing
    def add_peer_subscriptions(self, char* peer, char* prefix, char* bus):
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


    #At Publisher
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
            if subscription and cy_is_prefix_in_topic(prefix, topic):
                subscribers |= subscription

        return subscribers

    #At subscriber
    def cy_peer_push(self, char* peer, char* sender, char* topic,
                      object headers=None, object message=None, char* bus=''):
        cdef htable* bs
        cdef htable* sub
        cdef object cb

        if(htable_get(_cy_subscriptions.bu, peer) is not NULL):
            #if debug: print("here 22")
            bs = <htable*>htable_get(_cy_subscriptions.bu, peer)
            if(htable_get(bs, bus) is not NULL):
                #if debug: print("here 42")
                sub = <htable*>htable_get(bs, bus)
                if(htable_get_cb(sub, topic) is not NULL):
                    if debug: print("here 62")
                    cb = <object>htable_get_cb(sub, topic)
                    if debug: print("PUSH CALLBACK: {0}".format(cb))
                    cb(peer, sender, bus, topic, headers, message)
        #return cb

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

