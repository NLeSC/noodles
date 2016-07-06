from .coroutine import coroutine

import inspect


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
    different thread points (either two different threads simultaneously, or
    the same thread at a different point of execution). The universal way of
    fixing this is by putting a Queue object in between.

    The other way around, having two passive ends, requires the insertion of a
    thread running the simple function:

        def patch(source, sink):
            for item in source:
                sink.send(item)
    """
    def __init__(self, fn, mode):
        self.fn = fn       # if mode == 'pull' else coroutine(fn)
        self.mode = mode   # 'send' or 'pull'
        if mode == 'send':
            self.mode = 'push'

    def __rshift__(self, other):
        return self.__join__(other)

    def __call__(self, *args):
        return self.fn(*args)


class pull(Haploid):
    def __init__(self, fn):
        self.source = fn
        super(pull, self).__init__(fn, 'pull')

    def __join__(self, other):
        if hasattr(other, 'source'):
            return pull(lambda *args: other.source(lambda: self.source(*args)))
        elif inspect.isfunction(other):
            return self >> pull_map(other)
        else:
            raise TypeError('Cannot join coroutines of different types.')


class push(Haploid):
    def __init__(self, fn, dont_wrap=False):
        if dont_wrap:
            self.sink = fn
        else:
            self.sink = coroutine(fn)
        super(push, self).__init__(self.sink, 'push')

    def __join__(self, other):
        if hasattr(other, 'sink'):
            return push(lambda *args: self.sink(lambda: other.sink(*args)),
                        dont_wrap=True)
        elif inspect.isfunction(other):
            return self >> push_map(other)
        else:
            raise TypeError('Cannot join coroutines of different types.')


def compose_2(f, g):
    def h(*args):
        a = g(*args)
        if a:
            return f(*a)
        else:
            return None

    return h


class composer:
    def __init__(self, f):
        self.f = f

    def __call__(self, *args):
        return self.f(*args)

    def __rshift__(self, other):
        return composer(compose_2(other, self.f))


class pull_map(pull):
    def __init__(self, f):
        self.f = f
        super(pull_map, self).__init__(self.map)

    def __join__(self, other):
        if not isinstance(other, Haploid) and inspect.isfunction(other):
            return pull_map(compose_2(other, self.f))

        if isinstance(other, pull_map):
            return pull_map(compose_2(other.f, self.f))

        else:
            return super(pull_map, self).__join__(other)

    def map(self, source):
        for args in source():
            if args:
                yield self.f(*args)
            else:
                yield


class push_map(push):
    def __init__(self, f):
        self.f = f
        super(push_map, self).__init__(self.map)

    def __join__(self, other):
        if not isinstance(other, Haploid) and inspect.isfunction(other):
            return push_map(compose_2(other, self.f))

        if isinstance(other, push_map):
            return push_map(compose_2(other.f, self.f))

        else:
            return super(push_map, self).__join__(other)

    def map(self, sink):
        sink = sink()
        while True:
            args = yield
            if args:
                sink.send(self.f(*args))
            else:
                raise RuntimeError('Encountered `None` in push_map loop.')
                # sink.send(None)


def sink_map(f):
    @push
    def sink():
        while True:
            args = yield
            if args:
                f(*args)
            else:
                raise RuntimeError('Encountered `None` in sink_map loop.')

    return sink


def branch(*sinks_):
    @pull
    def junction(source):
        sinks = [s() for s in sinks_]

        for msg in source():
            for s in sinks:
                s.send(msg)
            yield msg

    return junction


def broadcast(*sinks_):
    @push
    def bc():
        sinks = [s() for s in sinks_]
        while True:
            msg = yield
            for s in sinks:
                s.send(msg)

    return bc


def patch(source, sink):
    """Create a direct link between a source and a sink."""
    sink = sink()
    for v in source():
        if v is not None:
            sink.send(v)
        else:
            raise RuntimeError("encountered None in stream")
