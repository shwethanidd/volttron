from libcpp.map cimport map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.set cimport set
from cython.operator cimport dereference, preincrement
import datetime

ctypedef void* vptr
ctypedef set[vptr] cfptr
cdef map[string, map[string, set[string]]] _my_peer_subscriptions

cdef class PubSubCy:
    cdef map[string, map[string, map[string, cfptr]]] _my_subscriptions
    cdef bint _debug

    def __cinit__(self):
        self._debug = False

    cpdef add_my_subscriptions(self, string peer, string prefix, object callback, string bus):
        cdef map[string, map[string, cfptr]] buses
        cdef map[string, cfptr] sub
        cdef cfptr cbset

        if(self._my_subscriptions.empty()):
            if self._debug: print("1 _my_subscriptions_empty {0}, {1}, {2}".format(peer, prefix, bus))
            cbset.insert(<void*>callback)
            sub[prefix] = <cfptr>cbset
            buses[bus] = sub
            self._my_subscriptions[peer] = buses
        else:
            if(self._my_subscriptions.find(peer) != self._my_subscriptions.end()):
                if self._debug: print("asd 1 {0}, {1}, {2}".format(peer, prefix, bus))
                buses = self._my_subscriptions[peer]

                if self._debug: print("Finding bus %s" % bus)
                if(self._my_subscriptions[peer].find(bus) != self._my_subscriptions[peer].end()):
                    sub = buses[bus]
                    if self._debug: print("Finding prefix %s" % prefix)
                    if(sub.find(prefix) != sub.end()):
                        if self._debug: print("Adding aother callback %s" % prefix)
                        cbset  = sub[prefix]
                        cbset.insert(<vptr>callback)
                        sub[prefix] = <cfptr>cbset
                        buses[bus] = sub
                        self._my_subscriptions[peer] = buses
                    else:
                        #if self._debug: print("Adding new prefix %s" % prefix)
                        cbset.insert(<vptr>callback)
                        sub[prefix] = <cfptr>cbset
                        buses[bus] = sub
                        self._my_subscriptions[peer] = buses
                else:
                    cbset.insert(<vptr>callback)
                    sub[prefix] = <cfptr>cbset
                    buses[bus] = sub
                    self._my_subscriptions[peer] = buses
            else:
                #if self._debug: print("bus %s" % bus)
                cbset.insert(<vptr>callback)
                sub[prefix] = <cfptr>cbset
                buses[bus] = sub
                self._my_subscriptions[peer] = buses

    #At peer, who is publishing
    cpdef add_peer_subscriptions(self, string peer, string prefix, string bus):
        cdef map[string, set[string]] sub
        cdef set[string] peerset
        cdef map[string, map[string, set[string]]].iterator it = _my_peer_subscriptions.begin()
        cdef set[string].iterator e
        cdef set[string].iterator i

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
                    if self._debug: print("PUBSUBCPPXX Insert peer: {0}".format(peer))
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
        cdef string prefix
        cdef set[string].iterator e
        cdef set[string].iterator i
        cdef string mytopic

        if self._debug: print("PUBSUBCPP In distribute: {0} {1} {2}".format(peer, topic, bus))

        if(_my_peer_subscriptions.find(bus) != _my_peer_subscriptions.end()):
            with nogil:
                sub = _my_peer_subscriptions[bus]
                end = sub.end()
                it = sub.begin()
                #if self._debug: print("PUBSUBCPP In distribute: s")
                while it != end:
                    prefix = dereference(it).first
                    mytopic = topic.substr(0, prefix.size())
                    #if self._debug: print("PUBSUBCPP In distribute: prefix: {0}, topic: {1}".format(prefix, mytopic))
                    if mytopic.compare(prefix) == 0:
                    #if self.is_prefix_in_topic(prefix, topic):
                        #if self._debug: print("PUBSUBCPP In distribute Found: {0}".format(prefix))
                        tempset= dereference(it).second
                        #peerset.insert(dereference(tempset.begin()))
                        e = tempset.end()
                        i= tempset.begin()
                        while i != e:
                            #if self._debug: print("In distribute Adding to peerset: {0}".format(dereference(i)))
                            peerset.insert(dereference(i))
                            preincrement(i)
                    preincrement(it)
        else:
            if self._debug: print("PUBSUBCPP Not found {}: ".format(bus))
        return peerset

    #At subscriber
    cpdef peer_push(self, string peer, string sender, object header, string topic, object message, string bus):
        cdef map[string, map[string, cfptr]] buses
        cdef map[string, cfptr] sub
        cdef object cb = None
        cdef map[string,cfptr].iterator end = sub.end()
        cdef map[string,cfptr].iterator it = sub.begin()
        cdef cfptr cbset
        cdef set[vptr].iterator end1 = cbset.end()
        cdef set[vptr].iterator it1 = cbset.begin()
        cdef string prefix
        cdef string mytopic

        if self._debug: print("PUBSUBCPP10 %s" % peer)
        with nogil:
            if(self._my_subscriptions.find(peer) != self._my_subscriptions.end()):
                #if self._debug: print("PUBSUBCPP10 Found peer %s" % peer)
                buses = self._my_subscriptions[peer]
                #if self._debug: print("PUBSUBCPPfinding bus {}".format(bus))
                if(buses.find(bus) != buses.end()):
                    #if self._debug: print("PUBSUBCPP12")
                    sub = buses[bus]
                    #if self._debug: print("PUBSUBCPPfinding topic: %s" % topic)
                    end = sub.end()
                    it = sub.begin()
                    while it != end:
                        prefix = dereference(it).first
                        #if self.is_prefix_in_topic(prefix, mytopic):
                        mytopic = topic.substr(0, prefix.size())
                        #if self._debug: print("PUBSUBCPP13 {0}, {1}".format(prefix, mytopic))
                        if mytopic.compare(prefix) == 0:
                            #if self._debug: print("PUBSUBCPP14 Found prefix {0} in topic: {1}".format(prefix, mytopic))
                            cbset = sub[prefix]
                            end1 = cbset.end()
                            it1 = cbset.begin()
                            while it1 != end1:
                                #if self._debug: print("PUBSUBCPP15 Found callback")
                                with gil:
                                    cb = <object>dereference(it1)
                                    cb(peer, sender, bus, topic, header, message)
                                preincrement(it1)
                        preincrement(it)

    def is_prefix_in_topic(self, prefix, topic):
        return topic[:len(prefix)] == prefix

    #Publisher
    cpdef publish(self, peer, header=None, topic=None, message=None, bus=""):
        #fill the header and pass to distribute
        self.distribute(peer, header, topic, message, bus)

