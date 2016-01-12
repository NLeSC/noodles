import numpy as np
from scipy.integrate import quad
from noodles import Storable


class Cosmology(Storable):
    """This object stores all relevant information wrt the background
    cosmology, parametrized by OmegaM, OmegaL and H0."""
    def __init__(self, H0, OmegaM, OmegaL):
        super(Cosmology, self).__init__()

        self.H0 = H0
        self.OmegaM = OmegaM
        self.OmegaL = OmegaL
        self.OmegaK = 1 - OmegaM - OmegaL
        self.grav_cst = 3./2 * OmegaM * H0**2
        self.factor = self._growing_mode_norm()

    def adot(self, a):
        return self.H0 * a * np.sqrt(
            self.OmegaL
            + self.OmegaM * a**-3
            + self.OmegaK * a**-2)

    def _growing_mode_norm(self):
        """result D(1) = 1. d/d0 + 0.001 = 1"""
        d = self.adot(1) * quad(lambda b: self.adot(b)**(-3), 0.00001, 1)[0]
        return 0.99999/d

    def growing_mode(self, a):
        if isinstance(a, np.ndarray):
            return np.array([self.growing_mode(b) for b in a])
        elif a <= 0.001:
            return a
        else:
            return self.factor * self.adot(a)/a * quad(
                lambda b: self.adot(b)**(-3), 0.00001, a)[0] \
                + 0.00001


LCDM = Cosmology(68.0, 0.31, 0.69)
EdS = Cosmology(70.0, 1.0, 0.0)
