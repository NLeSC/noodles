from noodles.lib import decorator
import math
from pytest import approx, raises


def test_decorator():
    @decorator
    def diff(f, delta=1e-6):
        def df(x):
            return (f(x + delta) - f(x - delta)) / (2 * delta)

        return df

    @diff
    def f(x):
        return x**2

    assert f(4) == approx(8)
    assert f(3) == approx(6)

    @diff(delta=1e-8)
    def g(x):
        return math.sin(x)

    assert g(0.5) == approx(math.cos(0.5))

    with raises(TypeError):
        @diff(r=10)
        def q(x):
            return x

    with raises(TypeError):
        @diff(30, 4)
        def r(x):
            return x
