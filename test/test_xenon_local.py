from nose.plugins.skip import SkipTest

try:
    import noodles
    from noodles.run.xenon import (run_xenon, XenonConfig, RemoteJobConfig, XenonKeeper)
    from noodles import serial
    from noodles.tutorial import (add, mul, sub, accumulate)

except ImportError:
    raise SkipTest("No pyXenon installed.")


def test_xenon_42():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    xenon_config = XenonConfig(
        jobs_scheme='local'
    )

    job_config = RemoteJobConfig(
        registry=serial.base,
        time_out=1
    )

    with XenonKeeper() as Xe:
        result = run_xenon(Xe, 2, xenon_config, job_config, C)
    
    assert(result == 42)

