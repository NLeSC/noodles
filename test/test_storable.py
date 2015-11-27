from noodles import schedule, run
from noodles.storable import Storable

from nose.tools import raises


class A(Storable):
    pass


class M(object):
    pass


@schedule
def f(x, y):
    return x + y


@schedule
def g(a, b):
    return a.x + b.x


def test_storable():
    a = A()
    b = A()

    a.x = 1
    b.x = f(3, 4)

    c = g(a, b)
    result = run(c)
    assert result == 8


@raises(TypeError)
def test_nonstorable():
    a = A()
    b = M()

    a.x = 1
    b.x = f(3, 4)

    c = g(a, b)
    result = run(c)
    assert result == 8
