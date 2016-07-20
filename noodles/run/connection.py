from .haploid import pull


class Connection(object):
    """
    Combine a source and a sink. These should represent the IO of
    some object, probably a worker. In this case the `source` is a
    coroutine generating results, while the sink needs to be fed jobs.
    """
    def __init__(self, source, sink, aux=None):
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
        self.aux = aux
        self.online = True

    def setup(self):
        """Activate the source and sink functions and return them in
        that order.

        :returns:
            source, sink
        :rtype: tuple"""
        src = self.source()
        snk = self.sink()
        return src, snk

    def __iter__(self):
        return iter((self.source, self.sink))

    def __rshift__(self, other):
        return self.__join__(other)

    def __join__(self, other):
        """A connection has one output channel, so the '>>' operator
        connects the source to a coroutine, creating a new connection."""
        return Connection(pull(lambda: other.fn(self.source)), self.sink)
