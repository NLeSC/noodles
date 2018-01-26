from .streams import (pull, patch)
from .queue import (Queue, EndOfQueue)
import threading
import functools


def thread_counter(finalize):
    """Modifies a thread target function, such that the number of active
    threads is counted. If the count reaches zero, a finalizer is called."""
    n_threads = 0
    lock = threading.Lock()

    def target_modifier(target):
        @functools.wraps(target)
        def modified_target(*args, **kwargs):
            nonlocal n_threads, lock

            with lock:
                n_threads += 1

            return_value = target(*args, **kwargs)

            with lock:
                n_threads -= 1
                if n_threads == 0:
                    finalize()

            return return_value

        return modified_target

    return target_modifier


def thread_pool(*workers, results=None, end_of_queue=EndOfQueue):
    """Returns a |pull| object, call it ``r``, starting a thread for each given
    worker.  Each thread pulls from the source that ``r`` is connected to, and
    the returned results are pushed to a |Queue|.  ``r`` yields from the other
    end of the same |Queue|.

    The target function for each thread is |patch|, which can be stopped by
    exhausting the source.

    If all threads have ended, the result queue receives end-of-queue.

    :param results: If results should go somewhere else than a newly
        constructed |Queue|, a different |Connection| object can be given.
    :type results: |Connection|

    :param end_of_queue: end-of-queue signal object passed on to the creation
        of the |Queue| object.

    :rtype: |pull|
    """
    if results is None:
        results = Queue(end_of_queue=end_of_queue)

    count = thread_counter(results.close)

    @pull
    def thread_pool_results(source):
        for worker in workers:
            t = threading.Thread(
                target=count(patch),
                args=(pull(source) >> worker, results.sink),
                daemon=True)
            t.start()

        yield from results.source()

    return thread_pool_results
