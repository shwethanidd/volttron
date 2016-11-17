from libcpp.map cimport map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.set cimport set
from libcpp.pair cimport pair
from cython.operator cimport dereference, preincrement
from zmq import green as zmq
from zmq import SNDMORE
from zmq.utils import jsonapi
from .... import jsonrpc
from base64 import b64encode, b64decode
import datetime

ctypedef void* vptr
ctypedef set[vptr] cfptr
ctypedef pair[string, string] mypair
ctypedef pair[string, cfptr] cbpair
ctypedef pair[string, map[string, set[string]]] prsubpair

cdef class PubSubCy:
    cdef map[string, map[string, map[string, cfptr]]] _my_subscriptions
    cdef map[string, map[string, set[string]]] _my_peer_subscriptions
    cdef bint _debug
    cdef object _socket

    def __cinit__(self):
        self._debug = False

    cpdef add_my_subscriptions(self, string peer, string prefix, object callback, string bus):
        cdef map[string, map[string, cfptr]] buses
        cdef map[string, cfptr] sub
        cdef cfptr cbset

        with nogil:
            if(self._my_subscriptions.empty()):
                #if self._debug: print("1 _my_subscriptions_empty {0}, {1}, {2}".format(peer, prefix, bus))
                cbset.insert(<void*>callback)
                sub[prefix] = <cfptr>cbset
                buses[bus] = sub
                self._my_subscriptions[peer] = buses
            else:
                if(self._my_subscriptions.find(peer) != self._my_subscriptions.end()):
                    #if self._debug: print("asd 1 {0}, {1}, {2}".format(peer, prefix, bus))
                    buses = self._my_subscriptions[peer]

                    #if self._debug: print("Finding bus %s" % bus)
                    if(self._my_subscriptions[peer].find(bus) != self._my_subscriptions[peer].end()):
                        sub = buses[bus]
                        #if self._debug: print("Finding prefix %s" % prefix)
                        if(sub.find(prefix) != sub.end()):
                            #if self._debug: print("Adding aother callback %s" % prefix)
                            cbset  = sub[prefix]
                            cbset.insert(<vptr>callback)
                            #sub[prefix] = <cfptr>cbset
                            sub.insert(dereference(new cbpair(prefix, cbset)))
                            buses[bus] = sub
                            self._my_subscriptions[peer] = buses
                        else:
                            #if self._debug: print("Adding new prefix {0} with callback {1}".format(prefix, callback))
                            cbset.insert(<vptr>callback)
                            #sub[prefix] = <cfptr>cbset
                            sub.insert(dereference(new cbpair(prefix, cbset)))
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
                    sub.insert(dereference(new cbpair(prefix, cbset)))
                    #sub[prefix] = <cfptr>cbset
                    buses[bus] = sub
                    self._my_subscriptions[peer] = buses
        #self.print_my_subscriptions(peer)

    #At peer, who is publishing
    cpdef add_peer_subscriptions(self, string peer, string prefix, string bus):
        cdef map[string, set[string]] sub
        cdef set[string] peerset
        cdef map[string, map[string, set[string]]].iterator it = self._my_peer_subscriptions.begin()
        cdef set[string].iterator e
        cdef set[string].iterator i

        with nogil:
            #if self._debug: print("PUBSUBCPPXX peer subs BUS {0}, {1}, {2}".format(peer, prefix, bus))
            if(self._my_peer_subscriptions.empty()):
                peerset.insert(peer)
                sub[prefix] = peerset
                self._my_peer_subscriptions[bus] = sub
                self._my_peer_subscriptions.insert(dereference(new prsubpair(bus, sub)))
                #self._my_peer_subscriptions.insert(it, (bus, sub))
            else:
                if(self._my_peer_subscriptions.find(bus) != self._my_peer_subscriptions.end()):
                    #if self._debug: print("PUBSUBCPPXXfound bus : {0}".format(bus))
                    sub = self._my_peer_subscriptions[bus]
                    if(sub.find(prefix) != sub.end()):
                        #if self._debug: print("PUBSUBCPPXXfound prefix: {0}".format(prefix))
                        peerset = sub[prefix]
                        #if self._debug: print("PUBSUBCPPXX Insert peer: {0}".format(peer))
                        peerset.insert(peer)
                        sub[prefix] = peerset
                        self._my_peer_subscriptions[bus] = sub
                    else:
                        #if self._debug: print("PUBSUBCPPXXpeer Adding prefix: {0}".format(prefix))
                        peerset.insert(peer)
                        sub[prefix] = peerset
                        self._my_peer_subscriptions[bus] = sub
                else:
                    #if self._debug: print("PUBSUBCPPXXpeer Adding bus: {0}".format(bus))
                    peerset.insert(peer)
                    sub[prefix] = peerset
                    self._my_peer_subscriptions[bus] = sub

    cpdef set_socket(self, socket):
        self._socket= socket

    #At subscriber
    cpdef distribute(self, string peer, string topic, object header, object message, string bus):
        cdef map[string, set[string]] sub
        cdef set[string] peerset, tempset
        cdef map[string,set[string]].iterator end = sub.end()
        cdef map[string,set[string]].iterator it = sub.begin()
        cdef string prefix
        cdef set[string].iterator e
        cdef set[string].iterator i
        cdef string mytopic

        if self._debug: print("PUBSUBCPP In distribute: {0} {1} {2}".format(peer, topic, bus))
        if(self._my_peer_subscriptions.find(bus) != self._my_peer_subscriptions.end()):
            with nogil:
                sub = self._my_peer_subscriptions[bus]
                #if self._debug: print("PUBSUBCPP In distribute: {0}".format(self._my_peer_subscriptions))
                end = sub.end()
                it = sub.begin()
                #if self._debug: print("PUBSUBCPP In distribute: s")
                while it != end:
                    prefix = dereference(it).first
                    mytopic = topic.substr(0, prefix.size())
                    #if self._debug: print("PUBSUBCPP In distribute: prefix: {0}, topic: {1}".format(prefix, mytopic))
                    if mytopic.compare(prefix) == 0 or mytopic == '':
                    #if self.is_prefix_in_topic(prefix, topic):
                        peerset = dereference(it).second
                        #if self._debug: print("PUBSUBCPP In distribute Peerset size: {0}".format(peerset.size()))
                    preincrement(it)
            self.send_to_peer(peerset, peer, topic, header, message, bus)
        else:
            if self._debug: print("PUBSUBCPP Not found {}: ".format(bus))

    cpdef send_to_peer(self, set[string] subscribers, string peer, string topic,
                    object headers, object message, string bus):
        cdef set[string].iterator end
        cdef set[string].iterator it

        if (subscribers.empty()):
            #if self._debug: print("subscribers empty")
            return
        else:
            if self._debug: print("PUBSUBCPP Forming json message")
            sender = self.encode_peer(peer)
            json_msg = jsonapi.dumps(jsonrpc.json_method(
                None, 'pubsub.push',
                [sender, bus, topic, headers, message], None))
            frames = [zmq.Frame(b''), zmq.Frame(b''),
                      zmq.Frame(b'RPC'), zmq.Frame(json_msg)]

            end = subscribers.end()
            it = subscribers.begin()

            while(it != end):
                subscriber = dereference(it)
                if self._socket:
                    if self._debug: print("PUBSUBCPP socket send json message to {}".format(subscriber))
                    self._socket.send(subscriber, flags=SNDMORE)
                    self._socket.send_multipart(frames, copy=False)
                preincrement(it)

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
                    #f self._debug: print("PUBSUBCPPfinding topic: %s" % topic)
                    end = sub.end()
                    it = sub.begin()
                    while it != end:
                        prefix = dereference(it).first
                        mytopic = topic.substr(0, prefix.size())
                        #if self._debug: print("PUBSUBCPP13 {0}, {1}".format(prefix, mytopic))
                        if mytopic.compare(prefix) == 0:
                            #if self._debug: print("PUBSUBCPP14 Found prefix {0} in topic: {1}".format(prefix, mytopic))
                            cbset = sub[prefix]
                            end1 = cbset.end()
                            it1 = cbset.begin()
                            while it1 != end1:
                                with gil:
                                    cb = <object>dereference(it1)
                                    #if self._debug: print("PUBSUBCPP15 Found callback {}".format(cb))
                                    cb(peer, sender, bus, topic, header, message)
                                preincrement(it1)
                        preincrement(it)

    cpdef map[string, map[string, vector[string]]] synchronize(self, string peer):
        cdef:
            map[string, map[string, vector[string]]] items
            map[string, cfptr] sub
            vector[string] prefixes
            map[string, map[string, cfptr]] buses
            map[string, map[string, map[string, cfptr]]].iterator it = self._my_subscriptions.begin()
            map[string, vector[string]] bs
            map[string, map[string, cfptr]].iterator it1
            map[string, cfptr].iterator it2 = sub.begin()
            string prefix, p
            map[string, map[string, vector[string]]].iterator itr

        if self._debug: print("SYNCHRONIZE Before synchronize op {}".format(peer))
        #self.print_my_subscriptions(peer)
        with nogil:
            if peer.empty():
                #if self._debug: print("SYNCHRONIZE Peer is empty: {}".format(peer))
                while(it != self._my_subscriptions.end()):
                    pr = dereference(it).first
                    buses = self._my_subscriptions[pr]
                    #if self._debug: print("SYNCHRONIZE For each peer: {0}, bus dict".format(pr))
                    it1 = buses.begin()
                    while(it1 != buses.end()):
                        sub = dereference(it1).second
                        bus = dereference(it1).first
                        #if self._debug: print("SYNCHRONIZE For each bus: {}".format(bus))
                        it2 = sub.begin()
                        while(it2 != sub.end()):
                            prefix = dereference(it2).first
                            prefixes.push_back(prefix)
                            preincrement(it2)
                        #if self._debug: print("for bus: {1}, Prefixes are {0} ".format(prefixes, bus))
                        bs[bus] = prefixes
                        prefixes.clear()
                        preincrement(it1)
                    items[pr] = bs
                    bs.clear()
                    preincrement(it)
            else:
                if(self._my_subscriptions.find(peer) != self._my_subscriptions.end()):
                    buses = self._my_subscriptions[peer]
                #For each peer, add map of <bus, list of prefixes>
                it1 = buses.begin()
                while(it1 != buses.end()):
                    sub = dereference(it1).second
                    bus = dereference(it1).first
                    #if self._debug: print("SYNCHRONIZE bus: {}".format(bus))
                    it2= sub.begin()
                    while(it2 != sub.end()):
                        prefix = dereference(it2).first
                        #if self._debug: print("SYNCHRONIZE prefix: {}".format(prefix))
                        prefixes.push_back(prefix)
                        preincrement(it2)
                    bs[bus] = prefixes
                    prefixes.clear()
                    preincrement(it1)
                items[peer] = bs
        if self._debug: print("SYNCHRONIZE After synchronize op {}".format(items))
        #self.print_my_subscriptions(peer)
        return items

    cpdef print_my_subscriptions(self, peer):
        cdef:
            map[string, map[string, map[string, cfptr]]].iterator it = self._my_subscriptions.begin()
            map[string, map[string, cfptr]].iterator it1
            map[string, cfptr].iterator it2
            map[string, cfptr] sub
            map[string, map[string, cfptr]] buses
            string prefix, pr
            object callback
            cfptr cbset
            set[vptr].iterator it3


        print("/******PRINT MY SUBSCRIPTIONS *******/")
        while (it != self._my_subscriptions.end()):
            pr = dereference(it).first
            print("PRINT MY SUBSCRIPTIONS {}".format(pr))
            buses = dereference(it).second
            it1 = buses.begin()
            while(it1 != buses.end()):
                sub = dereference(it1).second
                bus = dereference(it1).first
                print("PRINT MY SUBSCRIPTIONS bus: {}".format(bus))
                it2= sub.begin()
                while(it2 != sub.end()):
                    prefix = dereference(it2).first
                    cbset = <cfptr>dereference(it2).second
                    it3 = cbset.begin()
                    while it3 != cbset.end():
                        callback = <object>dereference(it3)
                        print("PRINT MY SUBSCRIPTIONS prefix {0} and callback {1}".format(prefix, callback))
                        preincrement(it3)
                    preincrement(it2)
                preincrement(it1)
            preincrement(it)

    cpdef sync(self, string peer, map[string, vector[string]] itms):
        cdef:
            vector[string] topics
            set[pair[string, string]] items
            set[pair[string, string]] removeitems
            map[string, vector[string]].iterator iter = itms.begin()
            map[string, set[string]] sub
            map[string, map[string, set[string]]].iterator it = self._my_peer_subscriptions.begin()
            map[string, set[string]].iterator it1 = sub.begin()
            vector[string].iterator vit
            string bus, prefix
            set[string] subscribers
            bint found =  False
            pair[string, string] bppair
            set[pair[string, string]].iterator itr, rit

        #if self._debug: print("SYNC peer {0}, items {1}".format(peer, itms))
        #if self._debug: print("SYNC Before sync Peer subscriptions: {}".format(self._my_peer_subscriptions))
        while(iter != itms.end()):
            bus = dereference(iter).first
            topics = dereference(iter).second
            vit = topics.begin()
            while(vit != topics.end()):
                prefix = dereference(vit)
                items.insert( dereference(new mypair(bus,prefix)) )
                preincrement(vit)
            preincrement(iter)

        #if self._debug: print("Items pair: {}".format(items))
        #Find the subscribers for each <bus, prefix> pair
        #If found, remove from items list
        #Else, remove stale subscribers
        it = self._my_peer_subscriptions.begin()
        while(it != self._my_peer_subscriptions.end()):
            sub = dereference(it).second
            bus = dereference(it).first
            it1 = sub.begin()
            while(it1 != sub.end()):
                found = False
                prefix = dereference(it1).first
                subscribers = dereference(it1).second
                bppair = dereference(new mypair(bus,prefix))
                if (items.find(bppair) != items.end() ):
                    #if self._debug: print("SYNC Erasing pair {}: ".format(bppair))
                    items.erase(items.find(bppair))
                    found = True
                    break
                if not found:
                    #if self._debug: print("SYNC Trying to erase {}: ".format(bppair))
                    if not (subscribers.empty()):
                        #if self._debug: print("SYNC Trying to erase {}: ".format(bppair))
                        if(subscribers.find(peer) != subscribers.end()):
                            #if self._debug: print("SYNC Erasing subscribers: {}".format(peer))
                            subscribers.erase(subscribers.find(peer))
                            sub[prefix] = subscribers
                            self._my_peer_subscriptions[bus] = sub
                        if (subscribers.empty()):
                            removeitems.insert( dereference(new mypair(bus,prefix)) )
                preincrement(it1)
            preincrement(it)

        #if self._debug: print("After remove operation Items pair: {}".format(items))
        #if self._debug: print("SYNC After Erasing subscribers : {}".format(self._my_peer_subscriptions))

        rit = removeitems.begin()
        while (rit != removeitems.end()):
            bus = dereference(rit).first
            prefix = dereference(rit).second
            sub = self._my_peer_subscriptions[bus]
            if not sub.empty():
                if(sub.find(prefix) != sub.end()):
                    sub.erase(sub.find(prefix))
                    self._my_peer_subscriptions[bus] = sub
            preincrement(rit)

        itr = items.begin()
        while(itr != items.end()):
            bus = dereference(itr).first
            prefix = dereference(itr).second
            self.add_peer_subscriptions(peer, bus, prefix)
            preincrement(itr)

    cpdef vector[string] drop_subscription(self, string peer, string prefix, object callback, string bus):
        cdef:
            vector[string] topics
            map[string, cfptr] sub
            map[string, cfptr].iterator it
            cfptr callbacks
            vector[string] remove_topic_subs
            vector[string].iterator vit
            string topic

        buses = self._my_subscriptions[peer]
        print("dropping subscription for {0}, {1}, {2}, {3}".format(peer, prefix, callback, bus))

        if (prefix.empty()):
            if callback is None:
                if (buses.find(bus) != buses.end()):
                    sub = buses[bus]
                    it = sub.begin()
                    while (it != sub.end()):
                        topics.push_back(dereference(it).first)
                        preincrement(it)
            else:
                if (buses.find(bus) != buses.end()):
                    sub = buses[bus]
                    it = sub.begin()
                    while (it != sub.end()):
                        topic = dereference(it).first
                        callbacks = dereference(it).second
                        if (callbacks.find(<vptr>callback) != callbacks.end()):
                            callbacks.erase(callbacks.find(<vptr>callback))
                            if self._debug: print("Callback to erase {}".format(callback))
                            sub[topic] = callbacks
                            buses[bus] = sub
                            self._my_subscriptions[peer] = buses
                        topics.push_back(topic)
                        if(callbacks.empty()):
                            remove_topic_subs.push_back(topic)
                        preincrement(it)
                    if self._debug: print("Prefix pushed to topics {}".format(topics))
                    if self._debug: print("Prefix pushed to remove_topic_subs {}".format(remove_topic_subs))
                    vit = remove_topic_subs.begin()
                    while (vit != remove_topic_subs.end()):
                        sub.erase(sub.find(dereference(vit)))
                        buses[bus] = sub
                        self._my_subscriptions[peer] = buses
                        preincrement(vit)

                    if (sub.empty()):
                        if self._debug: print("Found sub to be empty")
                        buses.erase(buses.find(bus))
                        self._my_subscriptions[peer] = buses
        else:
            if (buses.find(bus) != buses.end()):
                sub = buses[bus]
                if callback is None:
                    sub.erase(sub.find(prefix))
                else:
                    if (sub.find(prefix) != sub.end()):
                        callbacks = sub[prefix]
                        if (callbacks.find(<vptr>callback) != callbacks.end()):
                            callbacks.erase(callbacks.find(<vptr>callback))
                            if self._debug: print("Callback to erase {}".format(callback))
                        if(callbacks.empty()):
                            if self._debug: print("Callbacks empty")
                            sub.erase(sub.find(prefix))
                            buses[bus] = sub
                            self._my_subscriptions[peer] = buses
                topics.push_back(prefix)
                if self._debug: print("Prefix pushed to topics {}".format(prefix))
                if (sub.empty()):
                    if self._debug: print("sub empty ")
                    buses.erase(buses.find(bus))
                    self._my_subscriptions[peer] = buses
        if (buses.empty()):
            if self._debug: print("Buses empty ")
            self._my_subscriptions.erase(self._my_subscriptions.find(peer))
            if(self._my_subscriptions.find(peer) != self._my_subscriptions.end()):
                if self._debug: print("My Subscriptions for peer found".format(peer))
        return topics

    cpdef peer_unsubscribe(self, string peer, vector[string] prefixes, string bus):
        cdef:
            map[string, set[string]] sub
            map[string, set[string]].iterator it
            set[string] subscribers
            vector[string] remove_topic_subs
            vector[string].iterator vit, pit
            string topic, prefix

        sub = self._my_peer_subscriptions[bus]
        if self._debug: print("peer unsubscribe for {0}, {1}, {2}".format(peer, prefix, bus))
        if self._debug: print("Peer subscription before erase: {}".format(self._my_peer_subscriptions))
        if prefix.empty():
            it = sub.begin()
            while (it != sub.end()):
                topic = dereference(it).first
                subscribers = dereference(it).second
                if(subscribers.find(peer) != subscribers.end()):
                    subscribers.erase(subscribers.find(peer))
                    sub[topic] = subscribers
                    self._my_peer_subscriptions[bus] = sub
                if (subscribers.empty()):
                    remove_topic_subs.push_back(topic)
                preincrement(it)
            vit = remove_topic_subs.begin()
            while( vit != remove_topic_subs.end() ):
                sub.erase(sub.find(dereference(vit)))
                self._my_peer_subscriptions[bus] = sub
                preincrement(vit)

            if (sub.empty()):#optional
                self._my_peer_subscriptions.erase(self._my_peer_subscriptions.find(bus))
            if self._debug: print("Peer subscription after erase of peer: {0} is {1}".format(peer, self._my_peer_subscriptions))
        else:
            pit = prefixes.begin()
            while(pit != prefixes.end()):
                prefix = dereference(pit)
                if (sub.find(prefix) != sub.end()):
                    subscribers = sub[prefix]
                    if(subscribers.find(peer) != subscribers.end()):
                        subscribers.erase(subscribers.find(peer))
                        sub[prefix] = subscribers
                        self._my_peer_subscriptions[bus] = sub
                    if (subscribers.empty()):
                        sub.erase(sub.find(prefix))
                        self._my_peer_subscriptions[bus] = sub
                    if (sub.empty()):#optional
                        self._my_peer_subscriptions.erase(self._my_peer_subscriptions.find(bus))
                if self._debug: print("Peer subscription after erase of peer: {0} is {1}".format(peer, self._my_peer_subscriptions))

    cpdef peer_list(self, string peer, string prefix, string bus, bint subscribed, bint reverse):
        cdef:
            map[string, map[string, set[string]]] buses
            map[string, map[string, set[string]]].iterator it
            string bs, topic
            map[string, set[string]] sub
            map[string, set[string]].iterator it1
            set[string] subscribers
            bint ismember = False
            bint istopic = False

        if (bus.empty()):
            buses = self._my_peer_subscriptions
        else:
            buses[bus] = self._my_peer_subscriptions[bus]
        results = []
        it = buses.begin()
        while (it != buses.end()):
            bs = dereference(it).first
            sub = dereference(it).second
            it1 = sub.begin()
            while (it1 != sub.end()):
                topic = dereference(it1).first
                subscribers = dereference(it1).second
                if self._debug: print("Topic: {0}, Subscribers: {1}".format(topic, subscribers))
                if reverse:
                    istopic = self.is_prefix_in_topic(topic, prefix)
                else:
                    istopic = self.is_prefix_in_topic(prefix, topic)
                if istopic:
                    if(subscribers.find(peer) != subscribers.end()):
                        if self._debug: print("Found peer: {}".format(peer))
                        ismember = True
                    else:
                        ismember = False

                    if not subscribed or ismember:
                        results.append((bs, topic, ismember))
                        if self._debug: print("Appending results: {}".format(results))
                preincrement(it1)
            preincrement(it)
        return results

    cpdef add_bus(self, name):
        cdef:
            map[string, set[string]] sub

        if self._debug: print("Adding bus: {0}".format(name))
        self._my_peer_subscriptions[name] = sub

    cpdef remove_bus(self, name):
        if(self._my_peer_subscriptions.find(name) != self._my_peer_subscriptions.end()):
            self._my_peer_subscriptions.erase(self._my_peer_subscriptions.find(name))

    def is_prefix_in_topic(self, prefix, topic):
        return topic[:len(prefix)] == prefix

    def encode_peer(self, peer):
        if peer.startswith('\x00'):
            return peer[:1] + b64encode(peer[1:])
        return peer


