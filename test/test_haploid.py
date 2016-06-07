from noodles.run.haploid import (pull, push, push_map, pull_map, patch)


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
    print(list(inp()), " -> ", result)

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

    print(list(inp()), " -> ", result)
    assert result == [0, 1, 4, 9, 16]

