#Reference: [CAlg]C Algorithms library, http://c-algorithms.sourceforge.net/
# file: cqueue.pxd

#Remember to add export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
#All the required declarations from the queue.h
#need to be added here so that Cython (.pyx) can reference them
cdef extern from "libcalg-1.0/libcalg/queue.h":
    #Cython uses ctypedef for C typedef declarations
    ctypedef struct Queue:
        pass
    ctypedef void* QueueValue

    Queue* queue_new()
    void queue_free(Queue* queue)

    int queue_push_head(Queue* queue, QueueValue data)
    QueueValue  queue_pop_head(Queue* queue)
    QueueValue queue_peek_head(Queue* queue)

    int queue_push_tail(Queue* queue, QueueValue data)
    QueueValue queue_pop_tail(Queue* queue)
    QueueValue queue_peek_tail(Queue* queue)

    bint queue_is_empty(Queue* queue)
