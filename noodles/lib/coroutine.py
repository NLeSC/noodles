from functools import wraps


class EndOfWork(object):
    pass


def coroutine(f):
    """
    A sink should be send `None` first, so that the coroutine arrives
    at the `yield` position. This wrapper takes care that this is done
    automatically when the coroutine is started.
    """
    @wraps(f)
    def g(*args, **kwargs):
        sink = f(*args, **kwargs)
        sink.send(None)
        return sink

    return g
    
    
def close_coroutine(c):
    """Sends :py:class:`EndOfWork` to the coroutine, catching the expected
    :py:class:`StopIteration` exception."""
    try:
        c.send(EndOfWork)
    except StopIteration:
        pass
