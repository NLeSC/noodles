from .haploid import (pull, patch)
from .queue import (Queue)
from .protect import (CatchExceptions)
import threading


def thread_pool(*workers, results=None):
    """Threadpool should run functions. That means that both input and output
    need to be active mode, that this cannot be represented by a simple haploid
    co-routine.

    The resulting object should be able to replace a single worker in the
    chain, looking like::

        @haploid('pull')
        def worker(source):
            for job in source:
                yield run(job)

    To mend this, we run the required number of threads with `patch`, taking
    the workers as input source and a Queue sink as output. Then we yield from
    the Queue's source. The source that this is called with should then be
    thread-safe.
    """
    results = results if results is not None else Queue()

    @pull
    def fn(source):
        for s in workers:
            catch = CatchExceptions(results.sink)

            t = threading.Thread(
                target=catch(patch),
                args=(
                    lambda: (catch.job_source >> s)(source),
                    lambda: catch.result_sink(results.sink)),
                daemon=True)
            t.start()

        yield from results.source()

    return fn
