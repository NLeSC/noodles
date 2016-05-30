from noodles import schedule, run_single, unpack
from noodles.tutorial import add


@schedule
def f():
    return 1, 2, 3


def test_unpack_00():
    a, b, c = unpack(f(), 3)
    d = run_single(add(a, add(b, c)))
    assert d == 6

