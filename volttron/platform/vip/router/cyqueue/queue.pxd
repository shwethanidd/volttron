cimport cqueue
#-----------------------------------------------------------------------------
# Code declarations for queue
#-----------------------------------------------------------------------------
cdef class Queue:
    cdef cqueue.Queue* _c_queue
    # cpdef methods for direct-cython access
    cdef append(self, void* value)
    #Cython version of extend with count specified
    cdef c_extend(self, void** values, size_t count)
    #Pops the value at the head of the queue
    cdef void* pop(self) except *
    #Returns the value at the head of the queue
    cdef void* peek(self) except*
