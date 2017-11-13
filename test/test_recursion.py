from noodles import schedule, run_parallel, run_process, serial
from math import log, floor


@schedule
def mul(a, b):
    return a * b


@schedule
def factorial(n):
    if n == 0:
        return 1
    else:
        return mul(n, factorial(n - 1))


def test_recursion_parallel():
    f100 = factorial(50.0)
    result = run_parallel(f100, n_threads=1)
    print(result)
    assert floor(log(result)) == 148


def registry():
    return serial.pickle() + serial.base()


def test_recursion_process():
    f100 = factorial(50.0)
    result = run_process(f100, n_processes=1, registry=registry, verbose=False)
    print(result)
    assert floor(log(result)) == 148
