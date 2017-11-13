from noodles import (
        schedule, run_single, quote, unquote, run_process,
        schedule_hint, run_logging, find_first)
from noodles.tutorial import (add, sub, mul)
from noodles.serial import base
from noodles.display import NCDisplay


def cond(t, wt, wf):
    return s_cond(t, quote(wt), quote(wf))


@schedule
def s_cond(truth, when_true, when_false):
    if truth:
        return unquote(when_true)
    else:
        return unquote(when_false)


@schedule
def should_not_run():
    raise RuntimeError("This function should never have been called.")


def test_truthfulness():
    w = sub(4, add(3, 2))
    a = cond(True, w, should_not_run())
    b = cond(False, should_not_run(), w)
    result = run_single(mul(a, b))
    assert result == 1


counter = 0


def is_sixteen(n):
    return n == 16


@schedule
def counted_sqr(x):
    global counter
    counter += 1
    return x*x


@schedule_hint(display="squaring {x}", confirm=True)
def display_sqr(x):
    return x*x


def test_find_first():
    global counter

    wfs = [counted_sqr(x) for x in range(10)]
    w = find_first(is_sixteen, wfs)
    result = run_single(w)
    assert result == 16
    assert counter == 5

    wfs = [counted_sqr(x) for x in range(10)]
    w = find_first(is_sixteen, wfs)
    result = run_process(w, n_processes=1, registry=base)
    assert result == 16

    wfs = [display_sqr(x) for x in range(10)]
    w = find_first(is_sixteen, wfs)
    with NCDisplay() as display:
        result = run_logging(w, n_threads=2, display=display)
    assert result == 16
