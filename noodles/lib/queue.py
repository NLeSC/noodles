import queue
from .streams import (push, pull)
from .connection import Connection


class EndOfQueue(object):
    pass


class FlushQueue(object):
    pass


class Queue(Connection):
    """A |Queue| object hides a :py:class:`queue.Queue` object
    behind a source and sink interface.

    .. py:attribute:: sink

        Receives items that are put on the queue. Pushing the `end-of-queue`
        message through the sink will put it on the queue, and will also result
        in a :py:exc:`StopIteration` exception being raised.

    .. py:attribute:: source

        Pull items from the queue. When `end-of-queue` is encountered the
        generator returns after re-inserting the `end-of-queue` message on the
        queue for other sources to pick up. This way, if many threads are
        pulling from this queue, they all get the `end-of-queue` message.

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
        self._flush_queue = FlushQueue

        @push
        def sink():
            while True:
                r = yield
                self._queue.put(r)

                if r is self._flush_queue:
                    self.flush()
                    return

                if r is self._end_of_queue:
                    return

        @pull
        def source():
            while True:
                v = self._queue.get()
                if v is self._end_of_queue:
                    self._queue.task_done()
                    self._queue.put(self._end_of_queue)
                    return

                yield v
                self._queue.task_done()

        super(Queue, self).__init__(source, sink)

    def flush(self):
        """Erases queue and set `end-of-queue` message."""
        while not self._queue.empty():
            self._queue.get()
            self._queue.task_done()
        self.close()

    def close(self):
        """Sends `end_of_queue` message to the queue.
        Doesn't stop running sinks."""
        self._queue.put(self._end_of_queue)

    def empty(self):
        return self._queue.empty()

    def wait(self):
        self._queue.join()
