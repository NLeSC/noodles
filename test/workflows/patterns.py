from .workflow_factory import workflow_factory
from noodles import (
    patterns, schedule)
import math
import numpy as np


@workflow_factory(result=True, requires=['local', 'nocache'])
def fold_and_map():
    arr = np.random.normal(size=100)
    xs = patterns.fold(aux_sum, 0, arr)
    ys = patterns.map(lambda x: x ** 2, xs)

    return schedule(np.allclose)(ys, np.cumsum(arr) ** 2)


@workflow_factory(result=True, requires=['local', 'nocache'])
def map_filter_and_all():
    arr = np.random.normal(size=100)
    xs = patterns.map(lambda x: abs(x), arr)
    rs = patterns.filter(lambda x: x < 0.5, xs)

    return patterns.all(lambda x: x < 0.5, rs)


@workflow_factory(result=True, requires=['local', 'nocache'])
def zip_with():
    arr = np.random.normal(size=100)
    ys = patterns.map(lambda x: np.pi * x, arr)
    rs = patterns.zip_with(x_sin_pix, arr, ys)

    return schedule(np.allclose)(rs, arr * np.sin(np.pi * arr))


@workflow_factory(result=True, requires=['local', 'nocache'])
def map_any():
    arr = np.pi * np.arange(10., dtype=np.float64)
    xs = patterns.map(math.cos, arr)

    return patterns.any(lambda x: x < 0, xs)


def x_sin_pix(x, y):
    return x * math.sin(y)


def aux_sum(acc, x):
    r = acc + x
    return r, r
