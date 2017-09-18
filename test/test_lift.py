from noodles import (schedule, run_single, gather, lift)
from noodles.tutorial import (add, sub, mul)
from collections import OrderedDict


@schedule
def g(x):
    return x['a'] + x['b']

def test_lift_ordered_dict():
    x = OrderedDict()
    x['a'] = 1
    x['b'] = add(1, 2)
    y = g(lift(x))
    result = run_single(y)
    assert result == 4


class A:
    pass


@schedule
def f(a):
    return a.x + a.y


def test_lift_01():
    a = A()
    a.x = add(1, 2)
    a.y = sub(9, 11)
    b = f(lift(a))

    result = run_single(b)
    assert result == 1

