from noodles import (schedule, run_single, gather, lift)
from noodles.tutorial import (add, sub, mul)


class A:
    pass


@schedule
def f(a):
    return a.x + a.y


def test_lift_01():
    a = A()
    a.x = add(1, 2)
    a.y = sub(9, 11)
    b = f(lift(a))

    result = run_single(b)
    assert result == 1

