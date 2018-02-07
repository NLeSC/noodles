"""
Coroutine streaming module
==========================

.. note::
    In a break with tradition, some classes in this module have lower case
    names because they tend to be used as function decorators.

We use coroutines to communicate messages between different components
in the Noodles runtime. Coroutines can have input or output in two ways
*passive* and *active*. An example:

.. code-block:: python

    def f_pulls(coroutine):
        for msg in coroutine:
            print(msg)

    def g_produces(lines):
        for l in lines:
            yield lines

    lines = ['aap', 'noot', 'mies']

    f_pulls(g_produces(lines))

This prints the words 'aap', 'noot' and 'mies'. This same program could be
written where the co-routine is the one receiving messages:

.. code-block:: python

    def f_receives():
        while True:
            msg = yield
            print(msg)

    def g_pushes(coroutine, lines):
        for l in lines:
            coroutine.send(l)

    sink = f_receives()
    sink.send(None)  # the co-routine needs to be initialised
                     # alternatively, .next() does the same as .send(None)
    g_pushes(sink, lines)

The action of creating a coroutine and setting it to the first `yield`
statement can be performed by a little decorator:

.. code-block:: python

    from functools import wraps

    def coroutine(f):
        @wraps(f)
        def g(*args, **kwargs):
            sink = f(*args, **kwargs)
            sink.send(None)
            return sink

        return g

Pull and push
-------------

The |pull| and |push| classes capture the idea of pushing and pulling
coroutines, wrapping them in an object. These objects can then be chained
using the ``>>`` operator. Example:

.. code-block:: python

    >>> from noodles.lib import (pull_map, pull_from)
    >>> @pull_map
    ... def square(x):
    ...     return x*x
    ...
    >>> squares = pull_from(range(10)) >> square
    >>> list(squares)
    [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

Queues
------

Queues in python are thread-safe objects. We can define a new |Queue| object
that uses the python `queue.Queue` to buffer and distribute messages over
several threads:

.. code-block:: python

    import queue

    class Queue(object):
        def __init__(self):
            self._q = queue.Queue()

        def source(self):
            while True:
                msg = self._q.get()
                yield msg
                self._q.task_done()

        @coroutine
        def sink(self):
            while True:
                msg = yield
                self._q.put(msg)

        def wait(self):
            self.Q.join()

Note, that both ends of the queue are, as we call it, passive. We could make
an active source (it would become a normal function), taking a call-back as
an argument. However, we're designing the Noodles runtime so that it easy to
interleave functionality. Moreover, the `Queue` object is only concerned
with the state of its own queue. The outside universe is only represented by
the `yield` statements, thus preserving the principle of encapsulation.
"""

from .decorator import (
    decorator)

from .coroutine import (
    coroutine)

from .streams import (
    stream, pull, push, pull_map, push_map, sink_map,
    broadcast, branch, patch, pull_from, push_from)

from .connection import (
    Connection)

from .queue import (
    Queue, EndOfQueue, FlushQueue)

from .thread_pool import (
    thread_counter, thread_pool)

from .utility import (
    object_name, look_up, importable, deep_map, inverse_deep_map, unwrap,
    is_unwrapped)

__all__ = [
    'decorator', 'coroutine',
    'stream', 'pull', 'push', 'pull_map', 'push_map', 'sink_map',
    'broadcast', 'branch', 'patch', 'pull_from', 'push_from',
    'Connection', 'Queue', 'EndOfQueue', 'FlushQueue',
    'thread_pool', 'thread_counter',
    'object_name', 'look_up', 'importable', 'deep_map', 'inverse_deep_map',
    'unwrap', 'is_unwrapped']
