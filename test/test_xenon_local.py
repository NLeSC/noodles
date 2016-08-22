from nose.plugins.skip import SkipTest

try:
    # Only test xenon if it is installed
    from noodles.run.xenon import (XenonConfig, RemoteJobConfig, XenonKeeper)
except ImportError as e:
    raise SkipTest(str(e))
else:
    # Only test run_xenon_prov if provenance is installed, otherwise run_xenon
    try:
        from noodles.run.xenon import run_xenon_prov as run_xenon
    except ImportError:
        from noodles.run.xenon import run_xenon

import noodles
from noodles.display import (NCDisplay)
from noodles import serial
from noodles.tutorial import (mul, sub, accumulate)


@noodles.schedule_hint(display="{a} + {b}", confirm=True)
def log_add(a, b):
    return a + b


def test_xenon_42():
    A = log_add(1, 1)
    B = sub(3, A)

    multiples = [mul(log_add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    xenon_config = XenonConfig(
        jobs_scheme='local'
    )

    job_config = RemoteJobConfig(
        registry=serial.base,
        time_out=1000
    )

    with XenonKeeper() as Xe, NCDisplay() as display:
        result = run_xenon(
            C, Xe, "cache.json", 2, xenon_config, job_config,
            display=display)

    assert(result == 42)
