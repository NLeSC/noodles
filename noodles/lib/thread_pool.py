from .streams import (pull, patch)
from .queue import (Queue, EndOfQueue)
import threading


def thread_pool(*workers, results=None, end_of_queue=EndOfQueue):
    """Returns a |pull| object, call it ``r``, starting a thread for each given
    worker.  Each thread pulls from the source that ``r`` is connected to, and
    the returned results are pushed to a |Queue|.  ``r`` yields from the other
    end of the same |Queue|.

    The target function for each thread is |patch|, which can be stopped by
    exhausting the source.

    :param results: If results should go somewhere else than a newly constructed
    |Queue|, a different |Connection| object can be given.
    :type results: |Connection|

    :param end_of_queue: end-of-queue signal object passed on to the creation of
    the |Queue| object.

    :rtype: |pull|
    """
    if results is None:
        results = Queue(end_of_queue=EndOfQueue)

    @pull
    def thread_pool_results(source):
        for worker in workers:
            t = threading.Thread(
                target=patch,
                args=(source >> worker, results.sink),
                daemon=True)
            t.start()

        yield from results.source()

    return fn
