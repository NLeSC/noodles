import pytest

try:
    import numpy as np
    from numpy import (random, fft, exp)
    from noodles.serial.numpy import arrays_to_hdf5

    from noodles.run.run_with_prov import (
        run_parallel_opt)

except ImportError:
    has_numpy = False

else:
    has_numpy = True

from noodles.display import (NCDisplay)
from noodles import schedule, serial, schedule_hint


def registry():
    return serial.base() + arrays_to_hdf5()


@schedule_hint(display="fft", confirm=True, store=True)
def do_fft(a):
    return fft.fft(a)


@schedule
def make_kernel(n, sigma):
    return exp(-fft.fftfreq(n)**2 * sigma**2)


@schedule_hint(display="ifft", confirm=True, store=True)
def do_ifft(a):
    return fft.ifft(a).real


@schedule
def apply_filter(a, b):
    return a * b


@schedule_hint(display="make noise {seed}", confirm=True, store=True)
def make_noise(n, seed=0):
    random.seed(seed)
    return random.normal(0, 1, n)


def run(wf):
    with NCDisplay() as display:
        result = run_parallel_opt(
            wf, 2, registry, "cache.json", display=display)

    return result


@pytest.mark.skipif(not has_numpy, reason="NumPy needed.")
def test_hdf5():
    x = make_noise(256)
    k = make_kernel(256, 10)
    x_smooth = do_ifft(apply_filter(do_fft(x), k))
    result = run(x_smooth)

    assert isinstance(result, np.ndarray)
    assert result.size == 256
