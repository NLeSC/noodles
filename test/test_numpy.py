from nose.plugins.skip import SkipTest

try:
    import numpy as np
    from numpy import (random, fft, exp)

    from noodles.serial.numpy import arrays_to_hdf5
    from noodles.run.xenon import (XenonConfig, RemoteJobConfig, XenonKeeper)

except ImportError:
    raise SkipTest("No NumPy or Xenon installed.")

else:
    try:
        from noodles.run.xenon import run_xenon_prov as run_xenon
    except ImportError:
        from noodles.run.xenon import run_xenon

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
    xenon_config = XenonConfig(
        jobs_scheme='local'
    )

    job_config = RemoteJobConfig(
        registry=registry,
        time_out=1000
    )

    with XenonKeeper() as Xe, NCDisplay() as display:
        result = run_xenon(
            wf, Xe, "cache.json", 2, xenon_config, job_config,
            display=display, deref=True)

    return result


def test_hdf5():
    x = make_noise(256)
    k = make_kernel(256, 10)
    x_smooth = do_ifft(apply_filter(do_fft(x), k))
    result = run(x_smooth)

    assert isinstance(result, np.ndarray)
    assert result.size == 256
