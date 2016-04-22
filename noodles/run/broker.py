from .coroutines import (Connection, IOQueue, QueueConnection, patch, coroutine)
import threading


class Terminoid(object):
    pass


def haploid(mode):
    def wrap(f):
        return Haploid(f, mode)

    return wrap


class Haploid(object):
    """A Haploid is a single co-routine sending or pulling data.

    A pulling haploid could have the form::

        @haploid('pull')
        def foo(source):
            for item in source:
                yield do_something(item)

    while a sending haploid  (recognizable from the `send` call) would look
    like::

        @haploid('send')
        def foo(sink):
            while True:
                item = yield
                sink.send(do_something(item))

    The difference between these two modes is all about ownership of execution.
    If we want to link a haploid with active output (a sender) to a puller
    having active input, it is assumed the data transfer is approached from two
    different thread points (either two different threads simultaneously, or the
    same thread at a different point of execution). The universal way of fixing
    this is by putting a Queue object in between.

    The other way around, having two passive ends, requires the insertion of a
    thread running the simple function:

        def patch(source, sink):
            for item in source:
                sink.send(item)
    """
    def __init__(self, fn, mode):
        self.fn = fn if mode == 'pull' else coroutine(fn)
        self.mode = mode   # 'send' or 'pull'

    def __gt__(self, other):
        if not (self.mode == other.mode):
            raise RuntimeError('When linking haploids, their modes should match.')
        
        if self.mode == 'send':
            return Haploid(lambda outs: self.fn(other.fn(outs)), 'send')

        if self.mode == 'pull':
            return Haploid(lambda ins: other.fn(self.fn(ins)), 'pull')

    def __lt__(self, other):
        if not (self.mode == other.mode):
            raise RuntimeError('When linking haploids, their modes should match.')
        
        if self.mode == 'pull':
            return Haploid(lambda ins: self.fn(other.fn(ins)), 'pull')

        if self.mode == 'send':
            return Haploid(lambda outs: other.fn(self.fn(outs)), 'send')

    def __pos__(self):
        """Prepend a Queue to create a Connection with two passive ends."""
        Q = IOQueue()
        if self.mode == 'send':
            return Connection(Q.source, lambda: self.fn(Q.sink()))
        else:
            return Connection(lambda: self.fn(Q.source()), Q.sink)


class Diploid(object):
    """A Diploid is an object containing two haploids. In the case of our
    job queue system, a job is sent out and a result comes back. A broker
    should know about a worker having finished, so that we can send it another
    job; a logger needs to affirm that a job was run successfully; the
    provenance system needs to cache a result when it comes in but also act as a
    filter for outgoing jobs.

    This class is endowed with a the '//' operator. It joins the job haploid
    streams with the '>' operator and the result haploid streams with the '<'
    operator, creating a two-way traffic line.

    A diploid can be 'capped' with a worker, provided it has a matching io docks.
    This is done with the '|' operator, turning the resulting in a haploid.
    """
    def __init__(self, jobs, results):
        self.jobs = jobs
        self.results = results

    def __floordiv__(self, other):
        if isinstance(other, Diploid):
            if self.jobs.mode != other.jobs.mode and self.results.mode != other.results.mode:
                return Diploid(
                    self.jobs > other.jobs,
                    self.results < other.results)

    def __or__(self, other):
        if isinstance(other, Haploid):
            return self.jobs > other > self.results
        elif isinstance(other, tuple):
            return self | thread_pool(*other)


class Plug:
    def __init__(self, source, sink):
        self.source = source
        self.sink = sink


def tee(*recievers):
    @haploid('send')
    def fn(sink):
        while True:
            msg = yield
            for r in recievers:
                r.send(msg)

    return fn


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
        nonlocal results, stealers

        for s in stealers:
            t = threading.Thread(target=patch, args=(s(source), results.sink()))
            t.daemon = True
            t.start()

        yield from results.source()

    return fn


# The runners
from .scheduler import (Scheduler, Result)
from ..workflow import get_workflow

from itertools import repeat

@haploid('pull')
def worker(source):
    for key, job in source:
        try:
            if job.hints and 'annotated' in job.hints:
                result, meta_data = job.foo(*job.bound_args.args, **job.bound_args.kwargs)
                yield Result(key, 'done', result, meta_data)

            else:
                result = job.foo(*job.bound_args.args, **job.bound_args.kwargs)
                yield Result(key, 'done', result, None)

        except Exception as error:
            yield Result(key, 'error', None, error)


class JobKeeper(dict):
    def __init__(self):
        super(JobKeeper, self).__init__()
        # self['test'] = 'hi'

    def __setitem__(self, key, value):
        print('job-k:', key, value)
        super(JobKeeper, self).__setitem__(key, value)

    @coroutine
    def store_result(self):
        while True:
            result = yield
            if result.status != 'done':
                continue

            job = self[result.key]
            job.node.result = result.value


def branch(*sinks_):
    sinks = [s() for s in sinks_]

    @haploid('pull')
    def junction(source):
        for msg in source:
            for s in sinks:
                s.send(msg)
            yield msg

    return junction


def run_single(wf):
    J = JobKeeper()
    S = Scheduler(job_keeper=J)
    W = +(worker > branch(J.store_result))
    return S.run(W, get_workflow(wf))


def run_parallel(wf, n):
    return Scheduler().run(+thread_pool(*repeat(worker, n)), get_workflow(wf))


