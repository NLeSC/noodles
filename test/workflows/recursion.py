from .workflow_factory import workflow_factory
import noodles
from math import log, floor
from noodles.tutorial import add


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
def recursion():
    return floor_log(factorial(50.0))


@noodles.schedule
def fibonacci(n):
    if n < 2:
        return 1
    else:
        return add(fibonacci(n-1), fibonacci(n-2))


@workflow_factory(result=89)
def small_fibonacci():
    return fibonacci(10)


@workflow_factory(result=10946, requires=['prov'])
def dynamic_fibonacci():
    return fibonacci(20)
