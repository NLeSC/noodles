from noodles.run.xenon import (Machine, XenonJobConfig, run_xenon_simple)
from noodles import gather_all, schedule
from noodles.tutorial import (add, sub, mul)


def test_xenon_42(xenon_server):
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = schedule(sum)(gather_all(multiples))

    machine = Machine()
    worker_config = XenonJobConfig(verbose=True)

    result = run_xenon_simple(
        C, machine, worker_config)

    assert(result == 42)
