import numpy as np
from math import pi

tau = 2*pi


def md_cic(B, X_):
    X = X_ / B.res
    f = X - np.floor(X)

    rho = np.zeros(B.shape, dtype='float64')
    rho_, x_, y_ = np.histogram2d(
        X[:, 0] % B.N, X[:, 1] % B.N,
        bins=B.shape,
        range=[[0, B.N], [0, B.N]],
        weights=(1 - f[:, 0]) * (1 - f[:, 1]))

    rho += rho_
    rho_, x_, y_ = np.histogram2d(
        (X[:, 0] + 1) % B.N, X[:, 1] % B.N,
        bins=B.shape,
        range=[[0, B.N], [0, B.N]],
        weights=(f[:, 0]) * (1 - f[:, 1]))

    rho += rho_
    rho_, x_, y_ = np.histogram2d(
        X[:, 0] % B.N, (X[:, 1] + 1) % B.N,
        bins=B.shape,
        range=[[0, B.N], [0, B.N]],
        weights=(1 - f[:, 0]) * (f[:, 1]))

    rho += rho_
    rho_, x_, y_ = np.histogram2d(
        (X[:, 0] + 1) % B.N, (X[:, 1] + 1) % B.N,
        bins=B.shape,
        range=[[0, B.N], [0, B.N]],
        weights=(f[:, 0])*(f[:, 1]))
    rho += rho_

    return rho


class Interp2D:
    "Reasonably fast bilinear interpolation routine"
    def __init__(self, data):
        self.data = data
        self.shape = data.shape

    def __call__(self, x):
        X1 = np.floor(x).astype(int) % self.shape
        X2 = np.ceil(x).astype(int) % self.shape
        xm = x % 1.0
        xn = 1.0 - xm

        f1 = self.data[X1[:, 0], X1[:, 1]]
        f2 = self.data[X2[:, 0], X1[:, 1]]
        f3 = self.data[X1[:, 0], X2[:, 1]]
        f4 = self.data[X2[:, 0], X2[:, 1]]

        return \
            f1 * xn[:, 0] * xn[:, 1] + \
            f2 * xm[:, 0] * xn[:, 1] + \
            f3 * xn[:, 0] * xm[:, 1] + \
            f4 * xm[:, 0] * xm[:, 1]


def gradient_2nd_order(F, i):
    return 1/12 * np.roll(F, 2, axis=i) \
        - 2/3 * np.roll(F, 1, axis=i) \
        + 2/3 * np.roll(F, -1, axis=i) \
        - 1/12 * np.roll(F, -2, axis=i)
