from .coroutine import coroutine
from .decorator import decorator
import inspect
import sys


class Failure(object):
    pass


class stream(object):
    def __rshift__(self, other):
        return self.__join__(other)
        

class pull(stream):
    def __init__(self, fn):
        self.source = fn

    def __join__(self, other):
        if isinstance(other, pull):
            return pull(lambda x: other.source(lambda: self.source(x)))
        elif inspect.isfunction(other):
            return self >> pull_map(other)
        else:
            raise TypeError(
                'Don\'t know how to join {} and {}'.format(self, other))

    def __call__(self, x):
        return self.source(x)
                

class push(stream):
    def __init__(self, fn, dont_wrap=False):
        if dont_wrap:
            self.sink = fn
        else:
            self.sink = coroutine(fn)

    def __join__(self, other):
        if isinstance(other, push):
            return push(lambda x: self.sink(lambda: other.sink(x)),
                        dont_wrap=True)
        elif inspect.isfunction(other):
            return self >> push_map(other)
        else:
            raise TypeError(
                'Don\'t know how to join {} and {}'.format(self, other))


def compose_2(f, g):
    def h(x):
        return f(g(x))

    return h


class composer:
    def __init__(self, f):
        self.f = f

    def __call__(self, x):
        return self.f(x)

    def __rshift__(self, other):
        return composer(compose_2(other, self.f))


class pull_map(pull):
    def __init__(self, f):
        self.f = f
        super(pull_map, self).__init__(self.map)

    def __join__(self, other):
        if not isinstance(other, stream) and inspect.isfunction(other):
            return pull_map(compose_2(other, self.f))

        if isinstance(other, pull_map):
            return pull_map(compose_2(other.f, self.f))

        else:
            return super(pull_map, self).__join__(other)

    def map(self, source):
        yield from map(self.f, source())


class push_map(push):
    def __init__(self, f):
        self.f = f
        super(push_map, self).__init__(self.map)

    def __join__(self, other):
        if not isinstance(other, stream) and inspect.isfunction(other):
            return push_map(compose_2(other, self.f))

        if isinstance(other, push_map):
            return push_map(compose_2(other.f, self.f))

        else:
            return super(push_map, self).__join__(other)

    def map(self, sink):
        sink = sink()
        
        while True:
            x = yield
            sink.send(self.f(x))
                

def sink_map(f):
    @push
    def sink():
        while True:
            args = yield
            f(args)

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
        sink.send(v)
