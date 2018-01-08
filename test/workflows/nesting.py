from .workflow_factory import workflow_factory
import noodles


@noodles.schedule
def sqr(a):
    return a*a


@noodles.schedule
def sum(a, buildin_sum=sum):
    return buildin_sum(a)


@noodles.schedule
def map(f, lst):
    return noodles.gather_all(f(x) for x in lst)


@noodles.schedule
def num_range(a, b):
    return range(a, b)


@workflow_factory(result=285)
def test_higher_order():
    return sum(map(sqr, num_range(0, 10)))
