from .coroutine import coroutine
import inspect


class stream(object):
    """Base class for *pull* and *push* coroutines."""
    def __rshift__(self, other):
        return self.__join__(other)


class pull(stream):
    """A |pull| coroutine pulls from a source, yielding values.
    |pull| Objects can be chained using the `>>` operator.

    A |pull| object acts as a function of one argument, being the
    source that the coroutine will pull from. This source argument
    must always be a thunk (function of zero arguments) returning
    an iterable.

    .. |pull| replace:: :py:class:`pull`
    """
    def __init__(self, fn):
        self.source = fn

    def __iter__(self):
        return self.source()

    def __join__(self, other):
        if isinstance(other, pull):
            return pull(lambda *x: other.source(lambda: self.source(*x)))
        elif inspect.isfunction(other):
            return self >> pull_map(other)
        else:
            raise TypeError(
                'Don\'t know how to join {} and {}'.format(self, other))

    def __call__(self, *x):
        return self.source(*x)


class push(stream):
    """A |push| coroutine pushes to a sink, receiving values through ``yield``
    statements. |push| Objects can be chained using the `>>` operator.

    A |push| object acts as a function of one argument, being the sink that the
    coroutine will send to. This sink argument must always be a thunk (function
    of zero arguments) returning a coroutine.

    .. |push| replace:: :py:class:`push`
    """
    def __init__(self, fn, dont_wrap=False):
        if dont_wrap:
            self.sink = fn
        else:
            self.sink = coroutine(fn)

    def __lshift__(self, other):
        return other.__join__(self)

    def __join__(self, other):
        if isinstance(other, push):
            return push(lambda *x: self.sink(lambda: other.sink(*x)),
                        dont_wrap=True)
        elif inspect.isfunction(other):
            return self >> push_map(other)
        else:
            raise TypeError(
                'Don\'t know how to join {} and {}'.format(self, other))

    def __call__(self, *x):
        return self.sink(*x)


def compose_2(f, g):
    def h(*x):
        return f(g(*x))

    return h


class pull_map(pull):
    """A |pull_map| decorates a function of a single argument, to become
    a |pull| object. The resulting |pull| object pulls object from a source
    yielding values mapped through the given function.

    This is equivalent to::

        @pull
        def g(source):
            yield from map(f, source())

    where ``f`` is the function being decorated.

    The ``>>`` operator on this class is optimised such that only a single
    loop will be created when chained with another |pull_map|.

    Also, a |pull_map| may be chained to a function directly, including
    the given function in the loop.

    .. |pull_map| replace:: :py:class:`pull_map`
    """
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
    """A |push_map| decorates a function of a single argument, to become
    a |push| object. The resulting |push| object receives values through
    ``yield`` and sends them on after mapping through the given function.

    This is equivalent to::

        @push
        def g(sink):
            sink = sink()
            while True:
                x = yield
                sink.send(f(x))

    where ``f`` is the function being decorated.

    The ``>>`` operator on this class is optimised such that only a single
    loop will be created when chained with another |push_map|.

    Also, a |push_map| may be chained to a function directly, including
    the given function in the loop.

    .. |push_map| replace:: :py:class:`push_map`
    """
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
    """The |sink_map| decorator creates a |push| object from a function that
    returns no values. The resulting sink can only be used as an end point of a
    chain.

    Equivalent code::

        @push
        def sink():
            while True:
                x = yield
                f(x)

    .. |sink_map| replace:: :py:func:`sink_map`
    """
    @push
    def sink():
        while True:
            args = yield
            f(args)

    return sink


def branch(*sinks_):
    """The |branch| decorator creates a |pull| object that pulls from a single
    source and then sends to all the sinks given. After all the sinks received
    the message, it is yielded.

    .. |branch| replace:: :py:func:`branch`
    """
    @pull
    def junction(source):
        sinks = [s() for s in sinks_]

        for msg in source():
            for s in sinks:
                s.send(msg)
            yield msg

    return junction


def broadcast(*sinks_):
    """The |broadcast| decorator creates a |push| object that receives a
    message by ``yield`` and then sends this message on to all the given sinks.

    .. |broadcast| replace:: :py:func:`broadcast`
    """
    @push
    def bc():
        sinks = [s() for s in sinks_]
        while True:
            msg = yield
            for s in sinks:
                s.send(msg)

    return bc


def pull_from(iterable):
    """Creates a |pull| object from an iterable.

    :param iterable: an iterable object.
    :type iterable: :py:class:`~collections.abc.Iterable`
    :rtype: |pull|

    Equivalent to::

        pull(lambda: iter(iterable))
    """
    return pull(lambda: iterable)


def push_from(iterable):
    """Creates a |push| object from an iterable. The resulting function
    is not a coroutine, but can be chained to another |push|.

    :param iterable: an iterable object.
    :type iterable: :py:class:`~collections.abc.Iterable`
    :rtype: |push|
    """
    def p(sink):
        sink = sink()
        for x in iterable:
            sink.send(x)

    return push(p, dont_wrap=True)


def patch(source, sink):
    """Create a direct link between a source and a sink.

    Implementation::

        sink = sink()
        for value in source():
            sink.send(value)

    .. |patch| replace:: :py:func:`patch`
    """
    sink = sink()
    for v in source():
        try:
            sink.send(v)
        except StopIteration:
            return
