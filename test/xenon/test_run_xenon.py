from noodles.run.xenon import (Machine, XenonJobConfig, run_xenon_simple, run_xenon)
from noodles import gather_all, schedule
from noodles.tutorial import (add, sub, mul)


def test_xenon_42_simple(xenon_server):
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = schedule(sum)(gather_all(multiples))

    machine = Machine()
    worker_config = XenonJobConfig(verbose=True)

    result = run_xenon_simple(
        C, machine, worker_config)

    assert(result == 42)


def test_xenon_42_multi(xenon_server):
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = schedule(sum)(gather_all(multiples))

    machine = Machine()
    worker_config = XenonJobConfig(queue_name='multi', verbose=True)

    result = run_xenon(
        C, machine, worker_config, 2)

    assert(result == 42)
