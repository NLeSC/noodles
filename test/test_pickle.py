from noodles import schedule, run_process
from noodles.storable import PickleString

import numpy as np

class A(PickleString):
    def __init__(self, data):
        super(A, self).__init__()
        self.data = data

@schedule
def do_fft(a):
    return A(np.fft.fft(a.data))

@schedule
def make_kernel(n, sigma):
    return A(np.exp(-np.fft.fftfreq(n)**2 * sigma**2))

@schedule
def do_ifft(a):
    return A(np.fft.ifft(a.data).real)

@schedule
def apply_filter(a, b):
    return A(a.data * b.data)

@schedule
def make_noise(n):
    return A(np.random.normal(0, 1, n))

def test_pickle():
    x = make_noise(256)
    k = make_kernel(256, 10)
    x_smooth = do_ifft(apply_filter(do_fft(x), k))

    result = run_process(x_smooth, n_processes=1)

    assert isinstance(result.data, np.ndarray)
    assert result.data.size == 256
    # np.savetxt("curve.txt", result.data)
