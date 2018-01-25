import noodles
from noodles.tutorial import add, sub, mul, accumulate
from noodles import run_single


def test_get_intermediate_results():
    r1 = add(1, 1)
    r2 = sub(3, r1)

    def foo(a, b, c):
        return mul(add(a, b), c)

    r3 = [foo(i, r2, r1) for i in range(6)]
    r4 = accumulate(noodles.gather_all(r3))

    run_single(r4)

    assert noodles.result(r1) == 2
    assert noodles.result(r2) == 1
    assert [noodles.result(r) for r in r3] == [2, 4, 6, 8, 10, 12]
    assert noodles.result(r4) == 42
