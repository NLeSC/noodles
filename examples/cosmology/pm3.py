from noodles import schedule, Storable
from noodles.numpy_data import NumpyData

import numpy as np
from math import sqrt
from numpy import random
from numpy import fft

# from scipy.spatial import KDTree

from .maths import tau, Interp2D, md_cic, gradient_2nd_order
from .loops import apply_filter_2, potential_2


class BoxConfig(Storable):
    def __init__(self, dim, N, L):
        super(BoxConfig, self).__init__()

        self.dim = dim
        self.N = N
        self.L = L

        self.shape = (N,) * dim
        self.res = L / N
        self.k_max = (N * tau) / (2 * L)
        self.k_min = tau / L

    def as_dict(self):
        return {'dim': self.dim,
                'N': self.N,
                'L': self.L}

    @classmethod
    def from_dict(cls, dim, N, L):
        return cls(dim, N, L)


class Particles(Storable):
    def __init__(self, p):
        super(Particles, self).__init__()

        self._particles = NumpyData(p)

    @property
    def q(self):
        return self._particles.data[:, 0, :]

    @property
    def p(self):
        return self._particles.data[:, 1, :]

    @q.setter
    def q(self, n):
        self._particles.data[:, 0, :] = n

    @p.setter
    def p(self, n):
        self._particles.data[:, 1, :] = n


@schedule
def gaussian_random_field(box, P, seed=None):
    if seed is not None:
        random.seed(seed)

    white_noise = random.normal(0.0, 1.0, box.shape)
    F = fft.fftn(white_noise)
    apply_filter_2(box, lambda kx, ky: sqrt(P(sqrt(kx**2 + ky**2))), F)
    return NumpyData(fft.ifftn(F).real)


@schedule
def zeldovich_approximation(box, potential_):
    potential = potential_.data
    vx = gradient_2nd_order(potential, 0)
    vy = gradient_2nd_order(potential, 1)
    p = Particles(np.zeros(shape=[box.N**2, 2, 2], dtype=np.float64))
    p.q = np.indices(box.shape).transpose([1, 2, 0]).reshape([-1, 2]) * box.res
    p.p = np.array([vx, vy]).transpose([1, 2, 0]).reshape([-1, 2])
    return p


@schedule
def compute_density(box, particles):
    return NumpyData(md_cic(box, particles.q))


@schedule
def compute_potential(box, f_):
    f = f_.data
    F = fft.fftn(f)
    apply_filter_2(box, potential_2, F)
    return NumpyData(fft.ifftn(F).real)


@schedule
def drift(universe, particles, a, da):
    adot = universe.adot(a)
    particles.q += da * particles.p / (a**2 * adot)
    return particles


@schedule
def kick(box, universe, potential, particles, a, da):
    adot = universe.adot(a)

    for i in range(2):
        g = gradient_2nd_order(potential, i) / box.res * universe.grav_cst / a
        particles.p[:, i] -= da * Interp2D(g)(
            (particles.q / box.res) % box.N) / adot

    return particles
