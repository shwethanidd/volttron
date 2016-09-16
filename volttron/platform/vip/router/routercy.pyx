from libcpp.string cimport string
from libcpp.set cimport set
from libcpp.vector cimport vector
from cython.operator cimport dereference, preincrement
import os
import uuid
import logging
from logging import handlers
import logging.config
from zmq.utils.buffers cimport asbuffer_r
import sys

from zmq.utils import*
import zmq
from zmq import NOBLOCK, ZMQError, EINVAL, EHOSTUNREACH

from cysocket cimport Socket as CySocket
#from cymessage cimport Frame as cymessage.Frame
cimport cymessage
from queue cimport Queue


OUTGOING = 0
INCOMING = 1
UNROUTABLE = 2
ERROR = 3

cdef class BaseRouter:
    '''Abstract base class of VIP router implementation.

    Router implementers should inherit this class and implement the
    setup() method to bind to appropriate addresses, set identities,
    setup authentication, etc, etc. The socket will be created by the
    start() method, which will then call the setup() method.  Once
    started, the socket may be polled for incoming messages and those
    messages are handled/routed by calling the route() method.  During
    routing, the issue() method, which may be implemented, will be
    called to allow for debugging and logging. Custom subsystems may be
    implemented in the handle_subsystem() method. The socket will be
    closed when the stop() method is called.
    '''
    #_socket_class = zmq.Socket
    _socket_class = CySocket

    def __cinit__(self, context=None, default_user_id=None, **kwargs):
        '''Initialize the object instance.

        If context is None (the default), the zmq global context will be
        used for socket creation.
        '''
        print("BaseRouter cinit")
        self.context = zmq.Context.instance()
        if 'default_user_id' in kwargs:
            self.default_user_id = kwargs['default_user_id']
        else:
            self.default_user_id = None
        self.logger = logging.getLogger('cython.baserouter')
        if self.logger.level == logging.NOTSET:
            self.logger.setLevel(logging.DEBUG)
        self.OUTGOING = 0
        self.INCOMING = 1
        self.UNROUTABLE = 2
        self.ERROR = 3

    cpdef run(self):
        '''Main router loop.'''
        print("BaseRouter run")
        self.start()
        try:
            while self.poll():
                self.route()
        finally:
            print("BaseRouter stop()")
            self.stop()

    cpdef start(self):
        '''Create the socket and call setup().

        The socket is save in the socket attribute. The setup() method
        is called at the end of the method to perform additional setup.
        '''
        print("BaseRouter start()")
        self.socket = sock = self._socket_class(self.context, zmq.ROUTER)
        sock.router_mandatory = True
        sock.sndtimeo = 0
        sock.tcp_keepalive = True
        sock.tcp_keepalive_idle = 180
        sock.tcp_keepalive_intvl = 20
        sock.tcp_keepalive_cnt = 6
        self.setup()

    cpdef stop(self, int linger=1):
        '''Close the socket.'''
        self.socket.close(linger)

    cpdef setup(self):
        '''Called from start() method to setup the socket.

        Implement this method to bind the socket, set identities and
        options, etc.
        '''
        raise NotImplementedError()

    #@property
    cpdef poll(self):
        '''Returns the underlying socket's poll method.'''
        return self.socket.poll()

    #cpdef object handle_subsystem(self, object frames, object user_id):
    cpdef Queue handle_subsystem(self, Queue frames, object user_id):
        '''Handle additional subsystems and provide a response.

        This method does nothing by default and may be implemented by
        subclasses to provide additional subsystems.

        frames is a list of zmq.Frame objects with the following
        elements:

          [SENDER, RECIPIENT, PROTOCOL, USER_ID, MSG_ID, SUBSYSTEM, ...]

        The return value should be None, if the subsystem is unknown, an
        empty list or False (or other False value) if the message was
        handled but does not require/generate a response, or a list of
        containing the following elements:

          [RECIPIENT, SENDER, PROTOCOL, USER_ID, MSG_ID, SUBSYSTEM, ...]

        '''
        pass

    cpdef issue(self, int topic, object frames, object extra=None):
        pass

    if zmq.zmq_version_info() >= (4, 1, 0):
        def lookup_user_id(self, sender, recipient, auth_token):
            '''Find and return a user identifier.

            Returns the UTF-8 encoded User-Id property from the sender
            frame or None if the authenticator did not set the User-Id
            metadata. May be extended to perform additional lookups.
            '''
            # pylint: disable=unused-argument
            # A user id might/should be set by the ZAP authenticator
            try:
                return recipient.get('User-Id').encode('utf-8')
            except ZMQError as exc:
                if exc.errno != EINVAL:
                    raise
            return self.default_user_id
    else:
        def lookup_user_id(self, sender, recipient, auth_token):
            '''Find and return a user identifier.

            A no-op by default, this method must be overridden to map
            the sender and auth_token to a user ID. The returned value
            must be a string or None (if the token was not found).
            '''
            return self.default_user_id

    cdef _distribute(self, bytes subsys, bytes cmd, string peer):
        cdef:
            set[string] drop
            cymessage.Frame empty = cymessage.Frame(<char*>'')
            Queue frames = Queue()
            #object frames = [empty, empty, Frame(b'VIP1'), empty, empty]
            string pr
            set[string].iterator end = self._peers.end()
            set[string].iterator it = self._peers.begin()
            vector[string] peerlist
            vector[string].iterator it1 = peerlist.begin()
            set[string].iterator dit = drop.begin()
            char* subsys_data = NULL
            Py_ssize_t data_len_c=0
            char* cmd_data = NULL
            char* peer_data = NULL
            cymessage.Frame vipframe = cymessage.Frame(b'VIP')
            cymessage.Frame sysdata, cmdata, prdata

        frames.append(<void*>empty)
        frames.append(<void*>empty)
        frames.append(<void*>vipframe)
        frames.append(<void*>empty)
        frames.append(<void*>empty)
        asbuffer_r(subsys, <void **>&subsys_data, &data_len_c)
        asbuffer_r(cmd, <void **>&cmd_data, &data_len_c)
        asbuffer_r(peer, <void **>&peer_data, &data_len_c)
        sysdata = cymessage.Frame(subsys_data)
        cmdata = cymessage.Frame(cmd_data)
        prdata = cymessage.Frame(peer_data)

        frames.append(<void*>sysdata)
        frames.append(<void*>cmdata)
        frames.append(<void*>prdata)
        #frames.extend(Frame(f) for f in parts)
        #Send frames to all peers and drop it later
        while(it != end):
            pr = dereference(it)
            frames[0] = peer
            peerlist = self._send(frames)
            it1 = peerlist.begin()
            while(it1 != peerlist.end()):
                drop.insert(dereference(it1))
                preincrement(it1)
            preincrement(it)

        dit = drop.begin()

        while(dit != drop.end()):
            peer = dereference(dit)
            self._drop_peer(peer)
            preincrement(dit)

    cpdef _add_peer(self, string peer):
        cdef:
            set[string].iterator end = self._peers.end()
            set[string].iterator it = self._peers.begin()

        if(self._peers.find(peer) == self._peers.end()):
            return
        self._distribute(b'peerlist', b'add', peer)
        self._peers.insert(peer)

    cpdef _drop_peer(self, string peer):
        if (self._peers.find(peer) == self._peers.end()):
            self._peers.erase(self._peers.find(peer))
        self._distribute(b'peerlist', b'drop', peer)

    cpdef route(self):
        '''Route one message and return.

        One message is read from the socket and processed. If the
        recipient is the router (empty recipient), the standard hello
        and ping subsystems are handled. Other subsystems are sent to
        handle_subsystem() for processing. Messages destined for other
        entities are routed appropriately.
        '''
        cdef:
            CySocket socket
            object issue
            #object frames
            Queue frames = Queue()
            cdef cymessage.Frame sender, recipient, proto, auth_token, msg_id, name
            cdef cymessage.Frame hello, welcome, ping, pong, temp, ver, err, errnum
            cdef cymessage.Frame errmsg, subsystem, opr
            vector[string] peerlist
            vector[string].iterator it
            string peer

        socket = self.socket
        issue = self.issue
        # Expecting incoming frames:
        #   [SENDER, RECIPIENT, PROTO, USER_ID, MSG_ID, SUBSYS, ...]
        frames = socket.recv_multipart(copy=False)
        issue(self.INCOMING, frames)
        if frames.size() < 6:
            # Cannot route if there are insufficient frames, such as
            # might happen with a router probe.
            #if len(frames) == 2 and frames[0] and not frames[1]:
            if frames.size() == 2 and frames[0] and not frames[1]:
                issue(self.UNROUTABLE, frames, 'router probe')
                self._add_peer(frames[0].bytes)
            else:
                issue(self.UNROUTABLE, frames, 'too few frames')
            return

        sender = <cymessage.Frame>frames.pop()
        recipient = <cymessage.Frame>frames.pop()
        proto= <cymessage.Frame>frames.pop()
        auth_token= <cymessage.Frame>frames.pop()
        msg_id = <cymessage.Frame>frames.pop()

        if proto.bytes() != b'VIP1':
            # Peer is not talking a protocol we understand
            issue(self.UNROUTABLE, frames, 'bad VIP signature')
            return
        self._add_peer(sender.bytes())
        subsystem = <cymessage.Frame>frames.pop()
        if not recipient.bytes():
            # Handle requests directed at the router
            name = subsystem.bytes()
            if name == b'hello':
                #frames.clear()???
                #frames = [sender, recipient, proto, user_id, msg_id,
                #          b'hello', b'welcome', b'1.0', socket.identity, sender]
                frames.append(<void*>sender)
                frames.append(<void*>recipient)
                frames.append(<void*>proto)
                frames.append(<void*>user_id)
                frames.append(<void*>msg_id)
                hello = cymessage.Frame(b'hello')
                welcome =cymessage.Frame(b'welcome')
                ver = cymessage.Frame(b'1.0')
                frames.append(<void*>hello)
                frames.append(<void*>welcome)
                frames.append(<void*>ver)
                #frames.append(socket.identity) #To check
                frames.append(<void*>sender)
            elif name == b'ping':
                #frames.clear() ??
                frames.append(<void*>sender)
                frames.append(<void*>recipient)
                frames.append(<void*>proto)
                frames.append(<void*>user_id)
                frames.append(<void*>msg_id)
                ping = cymessage.Frame(b'ping')
                pong = cymessage.Frame(b'pong')
                frames.append(<void*>ping)
                frames.append(<void*>pong)
            elif name == b'peerlist':
                try:
                    opr = <cymessage.Frame> frames.pop()
                    op = opr.bytes()
                    #op = frames[6].bytes
                except IndexError:
                    op = None
                #frames.clear() ??
                frames.append(<void*>sender)
                frames.append(<void*>recipient)
                frames.append(<void*>proto)
                temp = cymessage.Frame(b'')
                frames.append(<void*>temp)
                frames.append(<void*>msg_id)
                frames.append(<void*>subsystem)
                if op == b'list':
                    listing = cymessage.Frame(b'listing')
                    frames.append(<void*>listing)
                    frames.append(<void*>recipient)
                    frames.append(<void*>listing)
                    frames.extend(self._peers) #???
                else:
                    error = (b'unknown' if op else b'missing') + b' operation'
                    err = cymessage.Frame(b'error')
                    frames.append(<void*>err)
                    frames.append(<void*>error)
            elif name == b'error':
                return
            else:
                response = self.handle_subsystem(frames, user_id)
                if response is None:
                    # Handler does not know of the subsystem
                    errnum, errmsg = error = _INVALID_SUBSYSTEM
                    issue(self.ERROR, frames, error)
                    frames.clear()
                    frames.append(<void*>sender)
                    frames.append(<void*>recipient)
                    frames.append(<void*>proto)
                    temp = cymessage.Frame(b'')
                    frames.append(<void*>temp)
                    frames.append(<void*>msg_id)
                    err = cymessage.Frame(b'error')
                    frames.append(<void*>err)
                    frames.append(<void*>errnum)
                    frames.append(<void*>errmsg)
                    frames.append(<void*>temp)
                    frames.append(<void*>subsystem)
                elif not response:
                    # Subsystem does not require a response
                    return
                else:
                    frames = response
        else:
            # Route all other requests to the recipient
            #frames.clear()
            frames.append(<void*>sender)
            frames.append(<void*>recipient)
            frames.append(<void*>proto)

        peerlist = self._send(frames)

        it = peerlist.begin()
        while(it != peerlist.end()):
            peer = dereference(it)
            self._drop_peer(peer)
            preincrement(it)

    cpdef Queue _send(self, Queue frames):
        cdef:
            object issue
            CySocket socket
            cymessage.Frame recipient, sender, proto, user_id, msg_id, subsystem
            cymessage.Frame erno, ermsg, err
            string errmsg, errnum
            Queue drop = Queue()
            Queue send_frames = Queue()
            bytes sendr, rec
        issue = self.issue
        socket = self.socket

        #recipient, sender = frames[:2]
        recipient = frames.at(0)
        sender = frames.at(1)
        # Expecting outgoing frames:
        #   [RECIPIENT, SENDER, PROTO, USER_ID, MSG_ID, SUBSYS, ...]
        try:
            # Try sending the message to its recipient
            socket.send_multipart(frames, flags=NOBLOCK, copy=False)
            issue(self.OUTGOING, frames)
        except ZMQError as exc:
            try:
                errnum, errmsg = error = _ROUTE_ERRORS[exc.errno]
            except KeyError:
                error = None
            if error is None:
                raise
            issue(ERROR, frames, error)
            if exc.errno == EHOSTUNREACH:
                rec = recipient.bytes()
                drop.append(<void*>rec)

            if exc.errno != EHOSTUNREACH or sender is not frames[0]:
                # Only send errors if the sender and recipient differ
                proto, user_id, msg_id, subsystem = frames[2:6]
                #frames = [sender, b'', proto, user_id, msg_id,
                #          b'error', errnum, errmsg, recipient, subsystem]
                frames.append(<void*>sender)
                frames.append(<void*>empty)
                frames.append(<void*>proto)
                frames.append(<void*>user_id)
                frames.append(<void*>msg_id)
                err = cymessage.Frame(b'error')
                frames.append(<void*>err)
                erno = cymessage.Frame(errnum)
                ermsg = cymessage.Frame(errmsg)
                frames.append(<void*>erno)
                frames.append(<void*>ermsg)
                frames.append(<void*>recipient)
                frames.append(<void*>subsystem)

                try:
                    socket.send_multipart(frames, flags=NOBLOCK, copy=False)
                    issue(self.OUTGOING, frames)
                except ZMQError as exc:
                    try:
                        errnum, errmsg = error = _ROUTE_ERRORS[exc.errno]
                    except KeyError:
                        error = None
                    if error is None:
                        raise
                    issue(ERROR, frames, error)
                    if exc.errno == EHOSTUNREACH:
                        sendr = sender.bytes()
                        drop.append(<void*>sendr)
        return drop
