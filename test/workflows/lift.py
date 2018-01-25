from .workflow_factory import workflow_factory
import noodles
from noodles.tutorial import (add, sub)
from collections import OrderedDict


@noodles.schedule
def g(x):
    return x['a'] + x['b']


@workflow_factory(result=4)
def lift_ordered_dict():
    x = OrderedDict()
    x['a'] = 1
    x['b'] = add(1, 2)
    return g(noodles.lift(x))


class A:
    pass


@noodles.schedule
def f(a):
    return a.x + a.y


@workflow_factory(result=1)
def lift_object():
    a = A()
    a.x = add(1, 2)
    a.y = sub(9, 11)
    return f(noodles.lift(a))
