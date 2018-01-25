from pytest import raises
from noodles.lib import (
    pull, push, pull_map, push_map, sink_map,
    broadcast, branch, patch, pull_from)


def test_pull_chaining():
    @pull
    def square(source):
        for x in source():
            yield x*x

    squares = pull_from(range(10)) >> square

    assert list(squares) == [i**2 for i in range(10)]


def test_pull_mapping():
    @pull_map
    def square(x):
        return x*x

    squares = pull_from(range(10)) >> square

    assert list(squares) == [i**2 for i in range(10)]


def test_function_chaining():
    squares = pull_from(range(10)) >> (lambda x: x*x)

    assert list(squares) == [i**2 for i in range(10)]


def test_wrong_chainging_raises_error():
    @push_map
    def square(x):
        return x*x

    with raises(TypeError):
        pull_from(range(10)) >> square


def test_push_chaining():
    def square(x):
        return x*x

    squares = []
    patch(pull_from(range(10)), push_map(square) >> sink_map(squares.append))

    assert squares == [i**2 for i in range(10)]


def test_branch():
    squares = []
    cubes = []

    square = push_map(lambda x: x**2) >> sink_map(squares.append)
    cube = push_map(lambda x: x**3) >> sink_map(cubes.append)
    numbers = list(pull_from(range(10)) >> branch(square, cube))
    assert numbers == list(range(10))
    assert cubes == [i**3 for i in range(10)]
    assert squares == [i**2 for i in range(10)]


def test_broadcast():
    result1 = []
    result2 = []
    sink = broadcast(sink_map(result1.append), sink_map(result2.append))
    patch(pull_from(range(10)), sink)

    assert result1 == result2 == list(range(10))


def test_pull_00():
    @pull
    def f(source):
        for i in source():
            yield i**2

    inp = pull(lambda: iter(range(5)))

    def out(lst):
        @pull
        def g(source):
            for i in source():
                lst.append(i)

        return g

    result = []
    pipeline = inp >> f >> out(result)
    pipeline()

    assert result == [0, 1, 4, 9, 16]


def test_push_00():
    @push
    def f(sink):
        sink = sink()
        while True:
            i = yield
            sink.send(i**2)

    inp = pull(lambda: iter(range(5)))

    def out(lst):
        @push
        def g():
            while True:
                i = yield
                lst.append(i)

        return g

    result = []
    pipeline = f >> out(result)
    patch(inp, pipeline)

    assert result == [0, 1, 4, 9, 16]
