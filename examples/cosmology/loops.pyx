cimport numpy as np
from libc.math cimport (exp, cos)


cdef double tau = 6.28318530717958647692


cdef int _wave_number(int N, int i):
    if i > N/2:
        return i - N
    else:
        return i


cpdef double complex potential_2(double kx, double ky):
    cdef double k2 = (kx*kx + ky*ky)
    if k2 > 0:
        return -1./k2
    else:
        return 1.0


cdef class power_2:
    cdef double power

    def __init__(self, power):
        self.power = power

    def __call__(self, double kx, double ky):
        cdef double k2 = (kx*kx + ky*ky)
        if k2 > 0:
            return k2**(self.power/2)
        else:
            return 1.0


cdef class compose_2:
    cdef object f, g

    def __init__(self, f, g):
        self.f = f
        self.g = g

    def __call__(self, kx, ky):
        return self.f(kx, ky) * self.g(kx, ky)


cdef class cutoff_2:
    cdef double k_max

    def __init__(self, box):
        self.k_max = box.k_max

    def __call__(self, double kx, double ky):
        cdef double k2 = (kx*kx + ky*ky)
        if k2 <= self.k_max**2:
            return 1
        else:
            return 0


cdef class scale_2:
    cdef double t
    cdef double res

    def __init__(self, object box, double sigma):
        self.t = (sigma / box.res)**2
        self.res = box.res

    def __call__(self, double kx, double ky):
        cdef double Gx = exp(self.t * (cos(kx * self.res) - 1.0))
        cdef double Gy = exp(self.t * (cos(ky * self.res) - 1.0))

        return Gx * Gy


def apply_filter_2(object box, object f, np.ndarray data):
    for j in range(box.N):
        ky = _wave_number(box.N, j) * tau/box.L

        for i in range(box.N):
            kx = _wave_number(box.N, i) * tau/box.L

            data[i, j] *= f(ky, kx)
