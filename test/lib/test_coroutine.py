from noodles.lib import coroutine


class EndOfWork(object):
    pass


def close_coroutine(x):
    try:
        x.send(EndOfWork)
    except StopIteration:
        pass


def test_coroutine():
    @coroutine
    def list_sink(lst):
        while True:
            value = yield
            if value is EndOfWork:
                return
            lst.append(value)

    a = []
    sink = list_sink(a)

    for i in range(10):
        sink.send(i)
    close_coroutine(sink)

    assert a == list(range(10))
