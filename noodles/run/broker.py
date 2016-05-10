from .coroutines import (Connection, IOQueue, QueueConnection, patch, coroutine)
import threading
from .haploid import (haploid, Haploid)
from .queue import (Queue)


def patchl(source, sink):
    """Create a direct link between a source and a sink."""
    sink = sink()
    for v in source():
        sink.send(v)


def thread_pool(*stealers):
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
    IOQueue's source. The source that this is called with should then be thread-
    safe.
    """
    results = IOQueue()

    @haploid('pull')
    def fn(source):
        for s in stealers:
            t = threading.Thread(
                target=patchl, 
                args=(lambda: s(source), results.sink))
            t.daemon = True
            t.start()

        yield from results.source()

    return fn


# The runners
from .scheduler import (Scheduler, Result)
from ..workflow import get_workflow
from .job_keeper import JobKeeper

from itertools import repeat, starmap
from functools import partial

#@haploid('pull')
#def worker(source):

def pull_map(f):
    @haploid('pull')
    def gen(source):
        return starmap(f, source())
    return gen


def send_map(f):
    @haploid('send')
    def crt(sink):
        sink = sink()
        while True:
            args = yield
            sink.send(f(*args))

    return crt


def sink_map(f):
    @haploid('send')
    def sink():
        while True:
            args = yield
            f(*args)

    return sink


@pull_map
def worker(key, job):
    """A worker coroutine. Pulls jobs, yielding results. If an
    exception is raised running the job, it returns a result
    object with 'error' status. If the job requests return-value
    annotation, a two-tuple is expected; this tuple is then
    unpacked, the first being the result, the second part is
    sent on in the error message slot."""
    try:
        if job.hints and 'annotated' in job.hints:
            result, meta_data = job.foo(
                    *job.bound_args.args, 
                    **job.bound_args.kwargs)
            return Result(key, 'done', result, meta_data)

        else:
            result = job.foo(*job.bound_args.args, **job.bound_args.kwargs)
            return Result(key, 'done', result, None)

    except Exception as error:
        return Result(key, 'error', None, error)


def branch(*sinks_):
    sinks = [s() for s in sinks_]

    @haploid('pull')
    def junction(source):
        for msg in source():
            for s in sinks:
                s.send(msg)
            yield msg

    return junction


def run_single(wf):
    J = JobKeeper()
    S = Scheduler(job_keeper=J)
    W = Queue() \
        .to(worker) \
        .to(branch(sink_map(J.store_result)))

    return S.run(W, get_workflow(wf))


def run_parallel(wf, n):
    J = JobKeeper()
    S = Scheduler(job_keeper=J)
    W = Queue() \
        .to(thread_pool(*repeat(worker, n))) \
        .to(branch(sink_map(J.store_result)))

    return S.run(W, get_workflow(wf))


@send_map
def log_job_start(key, job):
    return (key, 'start', job, None)


@send_map
def log_job_schedule(key, job):
    return (key, 'schedule', job, None)


def run_single_with_display(wf, display):
    S = Scheduler()
    W = Queue() \
        .to(branch(log_job_start.to(sink_map(display)))) \
        .to(worker) \
        .to(branch(sink_map(display)))

    return S.run(W, get_workflow(wf))


def run_parallel_with_display(wf, n, display):
    LogQ = Queue()

    S = Scheduler()
    
    t = threading.Thread(
        target=patchl, 
        args=(LogQ.source, sink_map(display)), 
        daemon=True).start()

    W = Queue() \
        .to(branch(log_job_start.to(LogQ.sink))) \
        .to(thread_pool(*repeat(worker, n))) \
        .to(branch(LogQ.sink))

    result = S.run(W, get_workflow(wf))
    LogQ.wait()
    del t

    return result

