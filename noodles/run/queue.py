import queue
from .haploid import (push, pull)
from .connection import Connection


class Queue(Connection):
    """
    We mock a server/client situation by creating a pipe object that
    recieves items in a sink, stores them in a synchronised queue
    object, and sends them out again in source. Any number of threads
    or objects may create a sink or source. All pool to the same Queue.

    This implementation serves as an example and to glue the local threaded
    runner together. On one side there is a worker pool, taking jobs from one
    of these queues. On the other side there is the controller taking results
    from a second pipe, the snake biting its tail.
    """
    def __init__(self, blocking=True):
        self.Q = queue.Queue()
        self.blocking = blocking

        @push
        def sink():
            while True:
                r = yield
                self.Q.put(r)

        @pull
        def source():
            while True:
                v = self.Q.get()
                yield v
                self.Q.task_done()

        super(Queue, self).__init__(source, sink)

    def empty(self):
        return self.Q.empty()

    def wait(self):
        self.Q.join()
