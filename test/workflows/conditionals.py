from .workflow_factory import workflow_factory
import noodles
from noodles.tutorial import (add, sub, mul)


def cond(t, wt, wf):
    return s_cond(t, noodles.quote(wt), noodles.quote(wf))


@noodles.schedule
def s_cond(truth, when_true, when_false):
    if truth:
        return noodles.unquote(when_true)
    else:
        return noodles.unquote(when_false)


@noodles.schedule
def should_not_run():
    raise RuntimeError("This function should never have been called.")


@workflow_factory(result=1)
def truthfulness():
    w = sub(4, add(3, 2))
    a = cond(True, w, should_not_run())
    b = cond(False, should_not_run(), w)
    return mul(a, b)


def is_sixteen(n):
    return n == 16


@noodles.schedule
def sqr(x):
    return x*x


@workflow_factory(result=16)
def find_first():
    wfs = [sqr(x) for x in range(10)]
    return noodles.find_first(is_sixteen, wfs)
