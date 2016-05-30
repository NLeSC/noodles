from .coroutine import coroutine

from itertools import starmap

def haploid(mode):
    def wrap(f):
        if mode == 'send':
            return Haploid(coroutine(f), mode)
        else:
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
        self.fn = fn # if mode == 'pull' else coroutine(fn)
        self.mode = mode   # 'send' or 'pull'

    def to(self, other):
        #   def __gt__(self, other):
        if (self.mode != other.mode):
            raise RuntimeError('When linking haploids, their modes should match.')
        
        if self.mode == 'send':
            return Haploid(lambda *args: self.fn(lambda: other.fn(*args)), 'send')

        if self.mode == 'pull':
            return Haploid(lambda *args: other.fn(lambda: self.fn(*args)), 'pull')

    def __lt__(self, other):
        if not (self.mode == other.mode):
            raise RuntimeError('When linking haploids, their modes should match.')
        
        if self.mode == 'pull':
            return Haploid(lambda *args: self.fn(lambda: other.fn(*args)), 'pull')

        if self.mode == 'send':
            return Haploid(lambda *args: other.fn(lambda: self.fn(*args)), 'send')

    def __call__(self, *args):
        return self.fn(*args)


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


def branch(*sinks_):
    @haploid('pull')
    def junction(source):
        sinks = [s() for s in sinks_]

        for msg in source():
            for s in sinks:
                s.send(msg)
            yield msg

    return junction


def patch(source, sink):
    """Create a direct link between a source and a sink."""
    sink = sink()
    for v in source():
        sink.send(v)

