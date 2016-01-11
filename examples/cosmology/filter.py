import numpy as np
from numbers import Number
from functools import reduce
import operator


class Filter:
    def __init__(self, f):
        self.f = f

    def __call__(self, K):
        return self.f(K)

    def __mul__(self, other):
        if isinstance(other, Filter):
            return Filter(lambda K: self.f(K) * other.f(K))

        elif isinstance(other, Number):
            return Filter(lambda K: other * self.f(K))

    def __pow__(self, n):
        return Filter(lambda K: self.f(K)**n)

    def __truediv__(self, other):
        if isinstance(other, Number):
            return Filter(lambda K: self.f(K) / other)

    def __add__(self, other):
        return Filter(lambda K: self.f(K) + other.f(K))

    def __invert__(self):
        return Filter(lambda K: self.f(K).conj())

    def abs(self, B, P):
        return np.sqrt(self.cc(B, P, self))

    def cc(self, B, P, other):
        return (~self * other * P)(B.K).sum().real / B.size * B.res**2

    def cf(self, B, other):
        return ((~self)(B.K) * other).sum().real / B.size * B.res**2


class Identity(Filter):
    def __init__(self):
        Filter.__init__(self, lambda K: 1)


class Zero(Filter):
    def __init__(self):
        Filter.__init__(self, lambda K: 0)


def _scale_filter(B, t):
    """returns discrete scale space filter, take care with units:
        [res] = Mpc / pixel, [k] = 1 / Mpc, [t] = Mpc**2"""
    def f(K):
        return reduce(
            lambda x, y: x*y,
            (np.exp(t / B.res**2 * (np.cos(k * B.res) - 1)) for k in K))
    return f


class Scale(Filter):
    def __init__(self, B, sigma):
        Filter.__init__(self, _scale_filter(B, sigma**2))


def _K_dot(X, K):
    return sum(X[i]*K[i] for i in range(len(X)))


class Pos(Filter):
    def __init__(self, x):
        Filter.__init__(self, lambda K: np.exp(-1j * _K_dot(x, K)))


class D(Filter):
    def __init__(self, n):
        def d(i):
            return Filter(lambda K: -1j * K[i])

        A = [d(int(i)-1) for i in str(n)]
        Filter.__init__(self, reduce(operator.mul, A))


def _K_pow(k, n):
    """raise |k| to the <n>-th power safely"""
    save = np.seterr(divide='ignore')
    a = np.where(k == 0, 0, k**n)
    np.seterr(**save)
    return a


class Power_law(Filter):
    def __init__(self, n):
        Filter.__init__(self, lambda K: _K_pow((K**2).sum(axis=0), n/2))


class Cutoff(Filter):
    def __init__(self, B):
        Filter.__init__(self, lambda K: np.where(
            (K**2).sum(axis=0) <= B.k_max**2, 1, 0))


class Potential(Filter):
    def __init__(self):
        Filter.__init__(self, lambda K: -_K_pow((K**2).sum(axis=0), -1.))
