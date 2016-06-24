"""
We use coroutines to handle the communication between the scheduler and
the different workers. Some of the functionality here may be reinventing
some batteries. If so, submit an issue and teach me the idiomatic way!
"""

from .coroutine import coroutine
from .connection import Connection

coroutine_sink = coroutine


class QueueConnection(Connection):
    """Takes an input and output queue, and conceptually links them,
    returning a pair containing a source from the input queue
    and a sink to the output queue.
    """
    def __init__(self, d_in, d_out):
        super(QueueConnection, self).__init__(d_in.source, d_out.sink)


def patch(source, sink):
    """Create a direct link between a source and a sink."""
    for v in source:
        sink.send(v)


@coroutine
def splice_sink(a, b):
    """A sink that sends its messages to both `a` and `b`."""
    while True:
        value = yield
        b.send(value)
        a.send(value)


def siphon_source(source, sink):
    """A source that yields from `source` and sends to `sink`. Consider this
    to be a wiretap."""
    for value in source:
        sink.send(value)
        yield value
