import noodles
from noodles.tutorial import (add, sub, mul, accumulate)
from noodles.display import (NCDisplay)
from noodles.run.runners import (
    run_single, run_parallel, run_parallel_with_display)


def test_broker_01():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    assert run_parallel(C, 4) == 42


def test_broker_02():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    assert run_single(C) == 42


@noodles.schedule_hint(display="{a} + {b}", confirm=True)
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

    with NCDisplay(title="Running the test") as display:
        assert run_parallel_with_display(C, 4, display) == 42
