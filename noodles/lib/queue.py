import queue
from .streams import (push, pull)
from .connection import Connection


class EndOfQueue(object):
    pass


class Queue(Connection):
    """A |Queue| object hides a :py:class:`queue.Queue` object
    behind a source and sink interface.

    :py:attribute:: sink
        Receives items that are put on the queue.

    :py:attribute:: source
        Pull items from the queue.

    .. |Queue| replace:: :py:class:`Queue`
    """
    def __init__(self, end_of_queue=EndOfQueue):
        """
        :param end_of_queue: When this object is encountered in both
        the sink and the source, their respective loops are terminated.
        Equality is checked using `is`; usualy this is a stub class
        designed especially for this purpose.
        """
        self._queue = queue.Queue()
        self._end_of_queue = end_of_queue

        @push
        def sink():
            while True:
                r = yield
                self._queue.put(r)

                if r is self._end_of_queue:
                    return

        @pull
        def source():
            while True:
                v = self.Q.get()
                yield v
                self.Q.task_done()

                if v is self._end_of_queue:
                    return

        super(Queue, self).__init__(source, sink)

    def empty(self):
        return self.Q.empty()

    def wait(self):
        self.Q.join()
