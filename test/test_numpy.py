from nose.plugins.skip import SkipTest

try:
    import numpy
    import numpy as np
    from numpy import (random, fft, exp)

    from noodles.serial.numpy import registry as numpy_registry

except ImportError:
    raise SkipTest("No NumPy installed.")


from noodles import schedule, run_process, serial
import os
from shutil import (copyfile, rmtree)


def registry():
    return serial.base() + numpy_registry(file_prefix='test-numpy/')


@schedule
def do_fft(a):
    return fft.fft(a)


@schedule
def make_kernel(n, sigma):
    return exp(-fft.fftfreq(n)**2 * sigma**2)


@schedule
def do_ifft(a):
    return fft.ifft(a).real


@schedule
def apply_filter(a, b):
    return a * b


@schedule
def make_noise(n):
    return random.normal(0, 1, n)

def test_pickle():
    x = make_noise(256)
    k = make_kernel(256, 10)
    x_smooth = do_ifft(apply_filter(do_fft(x), k))

    if os.path.exists("./test-numpy"):
        rmtree("./test-numpy")

    os.mkdir("./test-numpy")

    result = run_process(x_smooth, 1, registry, deref=True)

    assert isinstance(result, np.ndarray)
    assert result.size == 256

    # above workflow has five steps
    lst = os.listdir("./test-numpy")
    assert len(lst) == 5

    # remove the .npy files
    for f in lst:
        os.remove("./test-numpy/" + f)

    os.rmdir("./test-numpy")
