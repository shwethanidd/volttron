#[bus][prefix][peers]
from libc.stdlib cimport malloc, free, calloc
from libc.string cimport strcmp, strlen
from cpython.string cimport PyString_AsString
import datetime
import time

_my_peer_subscriptions = {}
#[peer][bus][prefix][callbacks]
#_my_subscriptions = {}
debug = False

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

#Subscriber
def subscribe(peer, prefix, callback, bus=''):
    add_my_subscriptions(peer, prefix, callback, bus)
    add_peer_subscriptions(peer, prefix, bus)


cdef add_my_subscriptions(char* peer, char* prefix, object callback, char* bus):
    cdef htable* bs
    cdef htable* sub
    cdef peers p
    cdef object cb
    cdef htable* fd
    #Find buses for given peer
    if debug: print("here 1")
    if(htable_get(_my_subscriptions.bu, peer) is NULL):
        if debug: print("here 2")
        sub = hm_create(5)
        htable_add(sub, <const void*>callback, prefix)
        bs = hm_create(5)
        htable_add(bs, sub, bus)
        htable_add(_my_subscriptions.bu, bs, peer)
    else:
        if debug: print("here 3")
        bs = <htable*>htable_get(_my_subscriptions.bu, peer)
        if(htable_get(bs, bus) is not NULL):
            if debug: print("here 4")
            sub = <htable*>htable_get(bs, bus)
            if(htable_get(sub, prefix) is not NULL):
                if debug: print("here 5")
                cb = <object>htable_get(sub, prefix)
            else:
                if debug: print("here 6")
                htable_add(sub, <const void*>callback, prefix)
        else:
            if debug: print("here 7")
            sub = hm_create(5)
            htable_add(sub, <const void*>callback, prefix)
            htable_add(bs, sub, bus)

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

def build_header():
    header = {}

    header['min-version'] = 1.0
    header['max-version'] = 3.5
    header['date'] = datetime.date.today()
    header['time'] = time.time()
    header['from'] = "sample sender"
    return header

def build_message():
        message = [{'OutsideAirTemperature3': 50.0, 'OutsideAirTemperature2': 50.0, 'OutsideAirTemperature1': 50.0, 'SampleBool2': True, 'EKG': 0.7431448254773941, 'SampleWritableShort1': 20, 'SampleWritableShort2': 20, 'SampleWritableShort3': 20, 'SampleWritableBool1': True, 'SampleWritableFloat1': 10.0, 'SampleWritableBool3': True, 'SampleWritableBool2': True, 'SampleLong3': 50, 'SampleLong2': 50, 'SampleWritableFloat2': 10.0, 'Heartbeat': True, 'SampleBool1': True, 'SampleLong1': 50, 'SampleBool3': True, 'SampleWritableFloat3': 10.0}, {'OutsideAirTemperature3': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'OutsideAirTemperature2': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'OutsideAirTemperature1': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool2': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'EKG': {'units': 'waveform', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort1': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort2': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort3': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool1': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat1': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool3': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool2': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong3': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong2': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat2': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}, 'Heartbeat': {'units': 'On/Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool1': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong1': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool3': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat3': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}}]
        return message

def is_prefix_in_topic( prefix, topic):
    return topic[:len(prefix)] == prefix

def my_devices_callback(header=None, topic=None, message=None):
    print("In my devices callback: Received {0} {1} {2}".format(header, topic, message))

def my_records_callback(header=None, topic=None, message=None):
    print("In my records callback: Received {0} {1} {2}".format(header, topic, message))

def publishtest():
    cdef int i = 0
    header = build_header()
    message = build_message()
    for i in range(100):
        print "Running publish test"
        publish('pubsub', header, 'devices', message, 'bus1')
        publish('xpub', header, 'records', message, 'bus1')
        i = i +1


