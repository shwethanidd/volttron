#[bus][prefix][peers]
from libcpp.map cimport map
from libcpp.string cimport string
from libcpp.vector cimport vector
from cython.operator cimport dereference, preincrement
import datetime

_my_peer_subscriptions = {}
ctypedef void* cfptr
#ctypedef void (*cfptr) (const void*, string, const void*, object)
cdef map[string, map[string, map[string, cfptr]]] _my_subscriptions
cdef bint debug = False

#Subscriber
def subscribe(peer, prefix, callback, bus):
    add_my_subscriptions(peer, prefix, callback, bus)
    add_peer_subscriptions(peer, prefix, bus)

cdef:
    struct hEntry:
        char* key
        void* data
        bint active

cdef add_my_subscriptions(string peer, string prefix, object callback, string bus):
    cdef map[string, map[string, cfptr]] buses
    cdef map[string, cfptr] sub

    if(_my_subscriptions.empty()):
        if debug: print("1 {0}, {1}, {2}".format(peer, prefix, bus))
        sub[prefix] = <cfptr>callback
        buses[bus] = sub
        _my_subscriptions[peer] = buses
    else:
        if(_my_subscriptions.find(peer) != _my_subscriptions.end()):
            if debug: print("asd 1 {0}, {1}, {2}".format(peer, prefix, bus))
            buses = _my_subscriptions[peer]

            if debug: print("Finding bus %s" % bus)
            if(_my_subscriptions[peer].find(bus) != _my_subscriptions[peer].end()):
                sub = buses[bus]
                if(sub.find(prefix) != sub.end()):
                    cback  = sub[prefix]
                else:
                    if debug: print("new prefix %s" % prefix)
                    sub[prefix] = <cfptr>callback
                    buses[bus] = sub
                    _my_subscriptions[peer] = buses
            else:
                sub[prefix] = <cfptr>callback
                buses[bus] = sub
                _my_subscriptions[peer] = buses
        else:
            if debug: print("bus %s" % bus)
            sub[prefix] = <cfptr>callback
            buses[bus] = sub
            _my_subscriptions[peer] = buses

#At peer, who is publishing
cdef add_peer_subscriptions(string peer, string prefix, string bus):
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
def publish(peer, header=None, topic=None, message=None, bus=""):
    #fill the header and pass to distribute

    distribute(peer, header, topic, message, bus)

#At subscriber
cdef distribute(string peer, object header, string topic, object message, string bus):
    peer_push(peer, header, topic, message, bus)

#At subscriber
cdef peer_push(string peer, object header, string topic, object message, string bus):
    cdef map[string, map[string, cfptr]] buses
    cdef map[string, cfptr] sub
    cdef object cb
    cdef map[string,cfptr].iterator end = sub.end()
    cdef map[string,cfptr].iterator it = sub.begin()

    if(_my_subscriptions.find(peer) != _my_subscriptions.end()):
        if debug: print("10 %s" % peer);
        buses = _my_subscriptions[peer]
        if debug: print("finding bus {}".format(bus))
        if(buses.find(bus) != buses.end()):
            if debug: print("12")
            sub = buses[bus]
            if debug: print("finding topic: %s" % topic)
            if(sub.find(topic) != sub.end()):
                 if debug: print("14")
                 cb = <object>sub[topic]
                 cb(header, topic, message)
                #end = sub.end()
                #it = sub.begin()
                #while it != end:
                #    print("deferencing {}".format(dereference(it).first))
                #    cb = <object>dereference(it).second
            #    preincrement(it)

cdef void callback_wrapper(const void* h, string t, const void* m, object mycallback):
    cdef object hd, msg
    hd = <object>h
    msg = <object>m
    if debug: print("Inside callback wrapper")
    mycallback(hd, t, msg)

def is_prefix_in_topic( prefix, topic):
    return topic[:len(prefix)] == prefix

def my_devices_callback(header=None, topic=None, message=None):
    print("In my devices callback: ")#Received {0} {1} {2}".format(header, topic, message))

def my_records_callback(header=None, topic=None, message=None):
    print("In my records callback: ")#Received {0} {1} {2}".format(header, topic, message))

def build_header():
    header = {}

    header['min-version'] = 1.0
    header['max-version'] = 3.5
    header['date'] = datetime.date.today()
    header['time'] = datetime.time.second
    header['from'] = "sample sender"
    return header

def build_message():
    message = {}
    message = [{'OutsideAirTemperature3': 50.0, 'OutsideAirTemperature2': 50.0, 'OutsideAirTemperature1': 50.0, 'SampleBool2': True, 'EKG': 0.7431448254773941, 'SampleWritableShort1': 20, 'SampleWritableShort2': 20, 'SampleWritableShort3': 20, 'SampleWritableBool1': True, 'SampleWritableFloat1': 10.0, 'SampleWritableBool3': True, 'SampleWritableBool2': True, 'SampleLong3': 50, 'SampleLong2': 50, 'SampleWritableFloat2': 10.0, 'Heartbeat': True, 'SampleBool1': True, 'SampleLong1': 50, 'SampleBool3': True, 'SampleWritableFloat3': 10.0}, {'OutsideAirTemperature3': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'OutsideAirTemperature2': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'OutsideAirTemperature1': {'units': 'F', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool2': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'EKG': {'units': 'waveform', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort1': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort2': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableShort3': {'units': '%', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool1': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat1': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool3': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableBool2': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong3': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong2': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat2': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}, 'Heartbeat': {'units': 'On/Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool1': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleLong1': {'units': 'Enumeration', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleBool3': {'units': 'On / Off', 'type': 'integer', 'tz': 'US/Pacific'}, 'SampleWritableFloat3': {'units': 'PPM', 'type': 'integer', 'tz': 'US/Pacific'}}]
    return message

def publishtest():
    cdef int i = 0
    header = build_header()
    message = build_message()
    for i in range(100):
        if debug: print "Running publish test"
        publish("pubsub", header, "devices", message, "bus1")
        publish("pubsub", header, "records", message, "bus1")
        i = i +1


