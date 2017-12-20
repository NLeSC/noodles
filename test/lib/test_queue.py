from noodles.lib import Queue, pull_map, patch, pull_from


def test_queue():
    Q = Queue
    patch(pull_from(range(10)) >> (lambda x: x*x), Q.sink)
    assert list(Q.source()) == [i*i for i in range(10)]
