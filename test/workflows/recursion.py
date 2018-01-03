from .workflow_factory import workflow_factory
import noodles
from math import log, floor


@noodles.schedule
def mul(a, b):
    return a * b


@noodles.schedule
def factorial(n):
    if n == 0:
        return 1
    else:
        return mul(n, factorial(n - 1))


@noodles.schedule
def floor_log(x):
    return floor(log(x))


@workflow_factory(result=148)
def test_recursion_parallel():
    return floor_log(factorial(50.0))
