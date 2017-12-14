import pytest

try:
    # Only test xenon if it is installed
    from noodles.run.xenon import (run_xenon, Machine, XenonJobConfig)
except ImportError as e:
    has_xenon = False
else:
    has_xenon = True

import noodles
from noodles.display import (NCDisplay)
from noodles import serial
from noodles.tutorial import (log_add, mul, sub, accumulate)


@pytest.mark.skipif(not has_xenon, reason="No (py)xenon installed.")
def test_xenon_42(xenon_server):
    A = log_add(1, 1)
    B = sub(3, A)

    multiples = [mul(log_add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    machine = Machine(
        scheduler_adaptor='local'
    )

    worker_config = XenonJobConfig(
        registry=serial.base,
        time_out=1000
    )

    result = run_xenon(
        C, machine, 2, worker_config)

    assert(result == 42)
