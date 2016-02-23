from noodles import schedule, run_single, run_process, serial
from noodles.storable import Storable, storable

from nose.tools import raises


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

    assert storable(a)

    a.x = 1
    b.x = f(3, 4)

    c = g(a, b)
    b.x = c
    d = h(b, a)

    result = run_process(d, n_processes=1, registry=serial.base, verbose=True)
    assert result.x == 7


@raises(TypeError)
def test_nonstorable():
    a = A()
    b = M()

    assert not storable(b)

    a.x = 1
    b.x = f(3, 4)

    c = g(a, b)
    result = run_single(c)
    assert result == 8
