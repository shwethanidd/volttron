import uuid
import logging
from logging import handlers
import logging.config
import os
import sys

from libcpp.string cimport string
from ..socket import decode_key, encode_key, Address
from ..tracking import Tracker
from zmq.utils import*
from routercy cimport BaseRouter
#from cysocket cimport Frame as cmessage.CyFrame
from queue import Queue
cimport cymessage
from queue cimport Queue

cdef class CyRouter(BaseRouter):
    cdef:
        bint _debug
        bint _monitor
        object _tracker
        object _secretkey
        object _local_address
        object addresses

    #def __cinit__(self, object local_address, addresses=(),
    #                object context = None, string secretKey='', object default_user_id= None,
    #                bint monitor = False, object tracker = None):
    def __cinit__(self, **kwargs):
        print("__cinit__ CyRouter")
        addresses = ()
        self.logger = logging.getLogger('cython.routercy')
        if self.logger.level == logging.NOTSET:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug("Setting logger")
        self._local_address = Address(kwargs['local_address'])
        #Not sure, check again
        if 'vip_address' in kwargs:
            addresses = kwargs['vip_address']
        else:
            addresses = ()
        self.addresses = addresses = [ Address(addr) for addr in addresses]

        if 'secretKey' in kwargs:
            self._secretkey = kwargs['secretKey']
        else:
            self._secretkey = None
        if 'monitor' in kwargs:
            self._monitor = kwargs['monitor']
        else:
            self._monitor = False
        if 'tracker' in kwargs:
            self._tracker = kwargs['tracker']
        else:
            self._tracker = None

    cpdef setup(self):
        cdef:
            object sock
            object addr
            object address

        self.logger.debug("setup CyRouter")
        print("setup RouterCy")
        sock = self.socket
        sock.identity = identity = str(uuid.uuid4())
        if self._monitor:
            Monitor(sock.get_monitor_socket()).start()
        sock.bind('inproc://vip')
        self.logger.debug('In-process VIP router bound to inproc://vip')
        print('In-process VIP router bound to inproc://vip')
        sock.zap_domain = 'vip'
        addr = self._local_address
        if not addr.identity:
            addr.identity = identity
        if not addr.domain:
            addr.domain = 'vip'
        addr.bind(sock)
        self.logger.debug('Local VIP router bound to %s' % addr)
        print('Local VIP router bound to %s' % addr)
        for address in self.addresses:
            if not address.identity:
                address.identity = identity
            if (address.secretkey is None and
                address.server not in ['NULL', 'PLAIN'] and
                self._secretkey):
                    address.server = 'CURVE'
                    address.secretkey = self._secretkey
            if not address.domain:
                address.domain = 'vip'
            address.bind(sock)
            self.logger.debug('Additional VIP router bound to %s' % address)

    cpdef issue(self, int topic, object frames, object extra=None):
        log = self.logger.debug

        formatter = FramesFormatter(frames)
        if topic == self.ERROR:
            errnum, errmsg = extra
            log('%s (%s): %s', errmsg, errnum, formatter)
        elif topic == self.UNROUTABLE:
            log('unroutable: %s: %s', extra, formatter)
        else:
            log('%s: %s',
                ('incoming' if topic == self.INCOMING else 'outgoing'), formatter)
        if self._tracker:
            self._tracker.hit(topic, frames, extra)


    cpdef Queue handle_subsystem(self, Queue frames, object user_id):
        cdef:
            Queue newframes = Queue()
            cymessage.Frame sndr, subsys, nm, empty, val, msgid
            bytes sender, subsystem, name
            int i=1
        # Expecting incoming frames:
        # [SENDER, RECIPIENT, PROTO, USER_ID, MSG_ID, SUBSYS, ...]
        tempframes.extend(frames, )
        sndr = <cymessage.Frame>frames.pop()
        newframes.append(<void*>sndr)
        sender = sndr.bytes()
        empty = cmessage.Frame(b'')
        while(i < 4):
            if(i==3):
                newframes.append(<void*>empty)
                frames.pop()
            newframes.append(frames.pop())
        subsys = <cymessage.Frame>frames.pop()
        newframes.append(<void*>subsys)
        subsystem = subsys.bytes()
        if subsystem == b'quit':
            #sender = frames[0].bytes
            if sender == b'control' and user_id == self.default_user_id:
                raise KeyboardInterrupt()
        elif subsystem == b'query':
            try:
                nm = <cymessage.Frame>frames.pop()
                newframes.append(<void*>nm)
                name = nm.bytes()
                #name = frames[6].bytes
            except IndexError:
                value = None
            else:
                if name == b'addresses':
                    if self.addresses:
                        value = [addr.base for addr in self.addresses]
                    else:
                        value = [self._local_address.base]
                elif name == b'local_address':
                    value = self._local_address.base
                else:
                    value = None

            newframes.append(<void*>empty)
            val = <cymessage.Frame>cmessage.Frame(jsonapi.dumps(value))
            newframes.append(<void*>val)
            return newframes

#cdef class FramesFormatter:
#    cdef Queue _frames
#    def __init__(self, frames):
#        pass
#    def __cinit__(self, Queue frames):
#        self._frames = frames
#    def __repr__(self):
#        lst = []
#        while(self._frames):
#            lst.append(self._frames.pop().bytes())
#        return str(lst)


class FramesFormatter(object):
    def __init__(self, frames):
        self.frames = frames

    def __repr__(self):
        return str([bytes(f) for f in self.frames.bytes])#check again
    __str__ = __repr__