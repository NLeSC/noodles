import noodles
from noodles import (schedule, run_single)
from noodles.delay import (delay, force)
from noodles.tutorial import (add, sub, mul, accumulate)


@schedule
def cond(truth, when_true, when_false):
    if truth:
        return force(when_true)
    else:
        return force(when_false)


@schedule
def should_not_run():
    raise RuntimeError("This function should never have been called.")


def test_truthfulness():
    w = sub(4, add(3, 2))
    a = cond(True, delay(w), delay(should_not_run()))
    b = cond(False, delay(should_not_run()), delay(w))
    result = run_single(mul(a, b))
    assert result == 1

