class Connection:
    """
    Combine a source and a sink. These should represent the IO of
    some object, probably a worker. In this case the `source` is a
    coroutine generating results, while the sink needs to be fed jobs.
    """
    def __init__(self, source, sink):
        """Connection constructor

        :param source:
            The source signal coroutine
        :type source: generator

        :param sink:
            The signal sink coroutine
        :type sink: sink coroutine
        """
        self.source = source
        self.sink = sink

    def setup(self):
        """Activate the source and sink functions and return them in
        that order.

        :returns:
            source, sink
        :rtype: tuple"""
        src = self.source()
        snk = self.sink()
        return src, snk

    def to(self, other):
        """A connection has one output channel, so the '>' operator
        connects the source to a coroutine, creating a new connection."""
        return Connection(lambda: other.fn(self.source), self.sink)

    def ot(self, other):
        return Connection(self.source, lambda: other.fn(self.sink))

