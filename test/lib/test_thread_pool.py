from noodles.lib import (thread_pool, Queue, pull_map, pull_from, patch)


def test_thread_pool():
    @pull_map
    def square(x):
        return x*x

    Q = Queue()
    worker = Q >> thread_pool(square, square)
    patch(pull_from(range(10)), worker.sink)
    Q.close()

    assert sorted(list(worker.source)) == [i**2 for i in range(10)]
