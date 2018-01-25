from noodles.lib import Queue, EndOfQueue, patch, pull_from
from pytest import raises


def test_queue():
    Q = Queue()
    patch(pull_from(range(10)) >> (lambda x: x*x), Q.sink)
    Q.close()
    assert list(Q.source) == [i*i for i in range(10)]
    with raises(StopIteration):
        next(Q.source())


def test_queue_chaining():
    Q = Queue() >> (lambda x: x*x)
    patch(pull_from(range(10)), Q.sink)
    try:
        Q.sink().send(EndOfQueue)
    except StopIteration:
        pass
    assert list(Q.source) == [i*i for i in range(10)]
