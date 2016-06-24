from libcpp.map cimport map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.set cimport set
from cython.operator cimport dereference, preincrement
import datetime

ctypedef void* cfptr
cdef map[string, map[string, set[string]]] _my_peer_subscriptions

cdef class PubSubCy:
    cdef map[string, map[string, map[string, cfptr]]] _my_subscriptions
    cdef bint _debug

    def __cinit__(self):
        self._debug = False

    cpdef add_my_subscriptions(self, string peer, string prefix, object callback, string bus):
        cdef map[string, map[string, cfptr]] buses
        cdef map[string, cfptr] sub

        if(self._my_subscriptions.empty()):
            if self._debug: print("PUBSUBCPP _my_subscriptions EMPTY {0}, {1}, {2}".format(peer, prefix, bus))
            sub[prefix] = <cfptr>callback
            buses[bus] = sub
            self._my_subscriptions[peer] = buses
        else:
            if(self._my_subscriptions.find(peer) != self._my_subscriptions.end()):
                if self._debug: print("PUBSUBCPPasd 1 {0}, {1}, {2}".format(peer, prefix, bus))
                buses = self._my_subscriptions[peer]
                if self._debug: print("PUBSUBCPPFinding bus %s" % bus)

                if(self._my_subscriptions[peer].find(bus) != self._my_subscriptions[peer].end()):
                    sub = buses[bus]
                    if(sub.find(prefix) != sub.end()):
                        cback  = sub[prefix]
                    else:
                        if self._debug: print("PUBSUBCPPnew prefix %s" % prefix)
                        sub[prefix] = <cfptr>callback
                        buses[bus] = sub
                        self._my_subscriptions[peer] = buses
                else:
                    sub[prefix] = <cfptr>callback
                    buses[bus] = sub
                    self._my_subscriptions[peer] = buses
            else:
                if self._debug: print("PUBSUBCPPbus %s" % bus)
                sub[prefix] = <cfptr>callback
                buses[bus] = sub
                self._my_subscriptions[peer] = buses

    #At peer, who is publishing
    cpdef add_peer_subscriptions(self, string peer, string prefix, string bus):
        cdef map[string, set[string]] sub
        cdef set[string] peerset
        cdef map[string, map[string, set[string]]].iterator it = _my_peer_subscriptions.begin()

        if self._debug: print("PUBSUBCPPXX peer subs BUS {0}, {1}, {2}".format(peer, prefix, bus))
        if(_my_peer_subscriptions.empty()):
            peerset.insert(peer)
            sub[prefix] = peerset
            #_my_peer_subscriptions[bus] = sub
            _my_peer_subscriptions.insert(it, (bus, sub))
        else:
            if(_my_peer_subscriptions.find(bus) != _my_peer_subscriptions.end()):
                if self._debug: print("PUBSUBCPPXXfound bus : {0}".format(bus))
                sub = _my_peer_subscriptions[bus]
                if(sub.find(prefix) != sub.end()):
                    if self._debug: print("PUBSUBCPPXXfound prefix: {0}".format(prefix))
                    peerset = sub[prefix]
                    peerset.insert(peer)
                    sub[prefix] = peerset
                    _my_peer_subscriptions[bus] = sub
                else:
                    if self._debug: print("PUBSUBCPPXXpeer Adding prefix: {0}".format(prefix))
                    peerset.insert(peer)
                    sub[prefix] = peerset
                    _my_peer_subscriptions[bus] = sub
            else:
                if self._debug: print("PUBSUBCPPXXpeer Adding bus: {0}".format(bus))
                peerset.insert(peer)
                sub[prefix] = peerset
                _my_peer_subscriptions[bus] = sub

    cpdef distr(self, string peer, string bus):
        if(_my_peer_subscriptions.find(bus) != _my_peer_subscriptions.end()):
            if self._debug: print("PUBSUBCPPXX Found bus!")
        else:
            if self._debug: print("PUBSUBCPPXX Bus not found {}".format(bus))

    #At subscriber
    cpdef set[string] distribute(self, string peer, string topic, object header, object message, string bus):
        cdef map[string, set[string]] sub
        cdef set[string] peerset, tempset
        cdef map[string,set[string]].iterator end = sub.end()
        cdef map[string,set[string]].iterator it = sub.begin()
        cdef string prefix, p
        cdef set[string].iterator e
        cdef set[string].iterator i

        if self._debug: print("PUBSUBCPP In distribute: {0} {1} {2}".format(peer, topic, bus))
        if(_my_peer_subscriptions.find(bus) != _my_peer_subscriptions.end()):
            sub = _my_peer_subscriptions[bus]
            end = sub.end()
            it = sub.begin()
            if self._debug: print("PUBSUBCPP In distribute: s")
            while it != end:
                prefix = dereference(it).first
                if self._debug: print("PUBSUBCPP In distribute: prefix: {0}, topic: {1}".format(prefix, topic))
                if self.is_prefix_in_topic(prefix, topic):
                    if self._debug: print("PUBSUBCPP In distribute: p")
                    if self._debug: print("PUBSUBCPP In distribute Found: {0}".format(prefix))
                    tempset= dereference(it).second
                    if self._debug: print("PUBSUBCPP In distribute Adding to peerset: {0}".format(dereference(tempset.begin())))
                    peerset.insert(dereference(tempset.begin()))
                preincrement(it)
        else:
            if self._debug: print("PUBSUBCPP Not found {}: ".format(bus))
        return peerset

    #At subscriber
    cpdef peer_push(self, string peer, string sender, object header, string topic, object message, string bus):
        cdef map[string, map[string, cfptr]] buses
        cdef map[string, cfptr] sub
        cdef object cb
        cdef map[string,cfptr].iterator end = sub.end()
        cdef map[string,cfptr].iterator it = sub.begin()

        if self._debug: print("PUBSUBCPP10 %s" % peer)
        if(self._my_subscriptions.find(peer) != self._my_subscriptions.end()):
            if self._debug: print("PUBSUBCPP10 Found peer %s" % peer)
            buses = self._my_subscriptions[peer]
            if self._debug: print("PUBSUBCPPfinding bus {}".format(bus))
            if(buses.find(bus) != buses.end()):
                if self._debug: print("PUBSUBCPP12")
                sub = buses[bus]
                if self._debug: print("PUBSUBCPPfinding topic: %s" % topic)
                end = sub.end()
                it = sub.begin()
                while it != end:
                    prefix = dereference(it).first
                    if self._debug: print("PUBSUBCPP13 {}".format(prefix))
                    if self.is_prefix_in_topic(prefix, topic):
                        if self._debug: print("PUBSUBCPP14 Found prefix {0} in topic: {1}".format(prefix, topic))
                        cb = <object>dereference(it).second#<object>sub[prefix]
                        cb(peer, sender, bus, topic, header, message)
                    preincrement(it)
        #return cb

    def is_prefix_in_topic(self, prefix, topic):
        return topic[:len(prefix)] == prefix

    #Publisher
    cpdef publish(self, peer, header=None, topic=None, message=None, bus=""):
        #fill the header and pass to distribute
        self.distribute(peer, header, topic, message, bus)

