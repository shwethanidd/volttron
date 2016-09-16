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
from cymessage cimport Frame as CyFrame
#from queue cimport Queue


cdef class BaseRouter:
    def __cinit__(self):
        print "hello"

    cdef route(self, CyFrame frm):
        cdef int x = 0
        x += 2