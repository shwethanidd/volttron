#[bus][prefix][peers]
from libcpp.map cimport map
from libcpp.string cimport string
from libcpp.vector cimport vector
from cython.operator cimport dereference, preincrement
from libc.stdlib cimport malloc, free, calloc

_my_peer_subscriptions = {}
#[peer][bus][prefix][callbacks]
#_my_subscriptions = {}
ctypedef void* cfptr
cdef map[string, map[string, map[string, cfptr]]] _my_subscriptions
cdef bint debug = True
#Subscriber
def subscribe(peer, prefix, callback, bus=''):
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
    cdef object cback
    cdef hEntry* temp

    print("1 %s" % peer)
    if(_my_subscriptions.empty() == False):
        if(_my_subscriptions.find(peer) != _my_subscriptions.end()):
            print("sdd1 %s" % peer)
            buses = _my_subscriptions[peer]
        else:
            _my_subscriptions[peer] = buses
    else:
        print("2")
        _my_subscriptions[peer] = buses
    if(buses.empty() == False):
        if(buses.find(bus) != buses.end()):
            sub = buses[bus]
        else:
            buses[bus] = sub
    else:
        print("3")
        buses[bus] = sub
    if(sub.empty() == False):
        if(sub.find(prefix) != sub.end()):
            cback  = <object>sub[prefix]
        else:
            sub[prefix] = <cfptr>callback
    else:
        print("4 %s" % prefix)
        temp = <hEntry*>malloc(sizeof(100))
        temp.data = <const cfptr>callback
        sub[prefix] = <cfptr>temp.data

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
def publish(peer, header=None, topic=None, message=None, bus=''):
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
cdef distribute(string peer, object header, string topic, object message, string bus):
    peer_push(peer, header, topic, message, bus)

#At subscriber
cdef peer_push(string peer, object header, string topic, object message, string bus):
    cdef map[string, map[string, cfptr]] buses
    cdef map[string, cfptr] sub
    cdef cfptr cb
    cdef object mycb

    if(_my_subscriptions.find(peer) != _my_subscriptions.end()):
        print("10 %s" % peer);
        buses = _my_subscriptions[peer]
        sub = buses[bus]
        if(buses.find(bus) != buses.end()):
            print("12")
            sub = buses[bus]
            print("topic: %s" % topic)
            cb = sub[topic]
            PyObject* mycb = <object>sub[topic][0]
            #cb(header, topic, message)
            if(sub.find(topic) != sub.end()):
                print("14")
                #cb = <object>sub[topic]
                #cb(header, topic, message)

def is_prefix_in_topic( prefix, topic):
    return topic[:len(prefix)] == prefix

def my_devices_callback(header=None, topic=None, message=None):
    print("In my devices callback: Received {0} {1} {2}".format(header, topic, message))

def my_records_callback(header=None, topic=None, message=None):
    print("In my records callback: Received {0} {1} {2}".format(header, topic, message))

def publishtest():
    cdef int i = 0
    while(i < 2):
        print "Running publish test"
        publish('pubsub', None, 'devices', None, 'bus1')
        publish('xpub', None, 'records/all/bogus', None, 'bus1')
        i = i +1


