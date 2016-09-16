from libcpp.string cimport string
from libcpp.set cimport set
from libcpp.vector cimport vector
from queue cimport Queue
cimport cymessage

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------
OUTGOING = 0
INCOMING = 1
UNROUTABLE = 2
ERROR = 3

cdef class BaseRouter:
    cdef:
        set[string] _peers
        object socket
        object context
        object default_user_id
        object logger
        int OUTGOING
        int INCOMING
        int UNROUTABLE
        int ERROR

    cdef route(self, cymessage.Frame frm)
    #cpdef run(self)
    #cpdef start(self)
    #cpdef stop(self, int linger=*)
    #cpdef setup(self)

    #cpdef poll(self)

    #cpdef object handle_subsystem(self, object frames, object user_id)

    #cpdef issue(self, int topic, object frames, object extra=*)

    #cdef _distribute(self, bytes subsys, bytes cmd, string peer)

    #cpdef _add_peer(self, string peer)

    #cpdef _drop_peer(self, string peer)

    #cpdef route(self)

    #cpdef Queue _send(self, Queue frames)
