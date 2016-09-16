"""0MQ Socket class declaration."""

#
#    Copyright (c) 2010-2011 Brian E. Granger & Min Ragan-Kelley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from zmq.backend.cython.socket cimport Socket as SocketBase

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

cdef class Socket(SocketBase):
    # cpdef methods for direct-cython access:
    cpdef send_multi(self, object msg_parts, int flags = *, copy = *, track = *, bint isFrame = *)
    cdef send_notracker(self, object data, int flags = *, bint copy = *)
    cdef int send_as_frames(self, object data, int flags = *)
    cpdef object recv(self, int flags=*, copy=*, track=*)
    cpdef poll(self, timeout=*, flags=*)
