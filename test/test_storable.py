from noodles import schedule, run_single, run_process, serial, lift
from noodles.storable import Storable
from pytest import raises


class A(Storable):
    def __init__(self):
        super(A, self).__init__()


class M(object):
    pass


@schedule
def f(x, y):
    return x + y


@schedule
def g(a, b):
    return a.x + b.x


@schedule
def h(a, b):
    c = A()
    c.x = a.x - b.x
    return c


def test_storable():
    a = A()
    b = A()

    a.x = 1
    b.x = f(3, 4)

    c = g(a, lift(b))
    b.x = c
    d = h(lift(b), a)

    result = run_process(d, n_processes=1, registry=serial.base)
    assert result.x == 7


def test_nonstorable():
    with raises(TypeError):
        a = A()
        b = M()

        a.x = 1
        b.x = f(3, 4)

        c = g(a, b)
        result = run_single(c)
        assert result == 8
