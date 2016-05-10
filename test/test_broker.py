import noodles
from noodles.tutorial import (add, sub, mul, accumulate)
from noodles.display import (NCDisplay)
from noodles.run import broker
import time


def test_broker_01():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    assert broker.run_parallel(C, 4) == 42


def test_broker_02():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    assert broker.run_single(C) == 42


@noodles.schedule_hint(display="│   {a} + {b}", confirm=True)
def log_add(a, b):
    return a + b


@noodles.schedule_hint(display="{msg}")
def message(msg, value=0):
    return value()


def test_broker_logging():
    A = log_add(1, 1)
    B = sub(3, A)

    multiples = [mul(log_add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))
    wf = message("\n╭─(Running the test)", lambda: C)

    with NCDisplay() as display:
        assert broker.run_parallel_with_display(wf, 4, display) == 42

