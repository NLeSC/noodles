from .haploid import (haploid, patch, send_map, pull_map)
from .queue import (Queue)
from .protect import (CatchExceptions)
import threading


def source_branch(*flst):
    @pull_map
    def g(*args):
        for f in flst:
            f(*args)
        return args

    return g


def sink_branch(*flst):
    @send_map
    def g(*args):
        for f in flst:
            f(*args)
        return args

    return g


def thread_pool(*workers):
    """Threadpool should run functions. That means that both input and output
    need to be active mode, that this cannot be represented by a simple haploid 
    co-routine.
    
    The resulting object should be able to replace a single worker in the chain,
    looking like::
        
        @haploid('pull')
        def worker(source):
            for job in source:
                yield run(job)
    
    To mend this, we run the required number of threads with `patch`, taking the
    workers as input source and a IOQueue sink as output. Then we yield from the
    Queue's source. The source that this is called with should then be thread-
    safe.
    """
    results = Queue()

    @haploid('pull')
    def fn(source):
        for s in workers:
            catch = CatchExceptions(results.sink)

            t = threading.Thread(
                target=catch(patch), 
                args=(
                    lambda: (source_branch(catch.job_pass).to(s))(source),
                    lambda: sink_branch(catch.result_pass)(results.sink)),
                daemon=True)
            t.start()

        yield from results.source()

    return fn

