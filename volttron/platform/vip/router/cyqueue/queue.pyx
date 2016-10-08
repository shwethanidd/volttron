#Reference: http://cython.readthedocs.io/en/latest/src/tutorial/clibraries.html
cimport cqueue
import time

cdef class Queue:
    """A queue class for C integer values."""

    #Internal pointer to c queue
    #cdef cqueue.Queue* _c_queue
    #constructor to initialize the queue pointer
    def __cinit__(self):
        self._c_queue = cqueue.queue_new()
        #queue returns NULL if no memory
        if self._c_queue is NULL:
            raise MemoryError()

    #To deallocate the queue memory after use
    def __dealloc__(self):
        if self._c_queue is not NULL:
            cqueue.queue_free(self._c_queue)

    #Append to end of queue
    cdef append(self, void* value):
        #queue_push_tail() returns 0 on error
        #due to insufficient memory
        if not cqueue.queue_push_tail(self._c_queue,
                                      <void*>value):
            raise MemoryError()

    #Cython version of extend with count specified
    cdef c_extend(self, void** values, size_t count):
        cdef size_t i
        for i in xrange(count):
            if not cqueue.queue_push_tail(
                    self._c_queue, <void*>values[i]):
                raise MemoryError()

    #Returns the value at the head of the queue.
    #Raises an exception if queue is empty
    cdef void* peek(self) except*:
        cdef void* value = \
            <void*>cqueue.queue_peek_head(self._c_queue)
        #cqueue returns NULL (cast to 0) if empty
        if value == NULL:
            # this may mean that the queue is empty
            if cqueue.queue_is_empty(self._c_queue):
                raise IndexError("Queue is empty")
        return value

    #Pops the value at the head of the queue
    cdef void* pop(self) except *:
        if cqueue.queue_is_empty(self._c_queue):
            raise IndexError("Queue is empty")
        return <void*>cqueue.queue_pop_head(self._c_queue)

    def __bool__(self):
        return not cqueue.queue_is_empty(self._c_queue)