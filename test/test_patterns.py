from noodles import (
    gather, patterns, run_parallel, schedule)
import math
import numpy as np


def test_pattern():
    """
    test functional patterns
    """
    wfs = [create_wf_1(), create_wf_2(), create_wf_3(),
           create_wf_4()]

    tests = run_parallel(gather(*wfs), 1)

    assert all(tests)


def create_wf_1():
    arr = np.random.normal(size=100)
    xs = patterns.fold(aux_sum, 0, arr)
    ys = patterns.map(lambda x: x ** 2, xs)

    return schedule_allclose(ys, np.cumsum(arr) ** 2)


def create_wf_2():
    arr = np.random.normal(size=100)
    xs = patterns.map(lambda x: abs(x), arr)
    rs = patterns.filter(lambda x: x < 0.5, xs)

    return patterns.all(lambda x: x < 0.5, rs)


def create_wf_3():
    arr = np.random.normal(size=100)
    ys = patterns.map(lambda x: np.pi * x, arr)
    rs = patterns.zip_with(x_sin_pix, arr, ys)

    return schedule_allclose(rs, arr * np.sin(np.pi * arr))


def create_wf_4():
    arr = np.pi * np.arange(10., dtype=np.float)
    xs = patterns.map(math.cos, arr)

    return patterns.any(lambda x: x < 0, xs)


def x_sin_pix(x, y):
    return x * math.sin(y)


@schedule
def schedule_allclose(arr, brr):
    fun = schedule(np.allclose)

    return fun(arr, brr)


def aux_sum(acc, x):
    r = acc + x
    return r, r
