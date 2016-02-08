from noodles import (
    schedule, Scheduler, gather,
    serial, Storable)
from noodles.serial import (Registry, AsDict)
from noodles.workflow import get_workflow
from noodles.run.process import process_worker


def registry():
    return Registry(parent=serial.base(), default=AsDict)


@schedule
def f(x, y):
    return x + y


@schedule
def ssum(lst, acc=sum):
    return acc(lst)


def test_worker():
    a = [f(i, j) for i in range(5) for j in range(5)]
    b = ssum(gather(*a))

    result = Scheduler().run(
        process_worker(registry),
        get_workflow(b))
    assert result == 100


class A(Storable):
    def __init__(self, **kwargs):
        super(A, self).__init__()
        self.__dict__.update(kwargs)


@schedule
def g(a):
    return a.x + a.y


@schedule
def cons(i, lst):
    return [i] + lst


def stupid_range(n, m):
    if n == m:
        return []
    else:
        return cons(n, stupid_range(n+1, m))


@schedule
def map(f, lst):
    return gather(*[f(i) for i in lst])


@schedule
def sqr(x):
    return x*x


@schedule
def concatenate(lst):
    return sum(lst, [])


# def test_stupid_range():
#     a = stupid_range(0, 5)
#     result1 = Scheduler().run(process_worker(registry), get_workflow(a))
#     assert result1 == list(range(5))
#
#     b = map(sqr, stupid_range(0, 5))
#     result2 = Scheduler().run(process_worker(registry), get_workflow(b))
#     assert result2 == [i*i for i in range(5)]


def dmap(f, lst):
    return gather(*[gather(*[
        f(x) for x in row]) for row in lst])


# def test_worker_with_storable():
#     a = [[A(y=j) for j in range(5)] for i in range(5)]
#     for i, lst in enumerate(a):
#         for q in lst:
#             q.x = f(i, q.y)
#
#     c = dmap(g, a)
#     b = ssum(concatenate(c))
#     result = Scheduler().run(process_worker(registry), get_workflow(b))
#     assert result == 150
