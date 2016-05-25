import noodles
from noodles.run.runners import (run_parallel_timing)
from noodles.tutorial import (mul, sub, accumulate)
import time
import sys

@noodles.schedule_hint(
    display="adding {a} + {b}")
def add(a, b):
    time.sleep(0.01)
    return a + b

def test_xenon_42():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(noodles.gather(*multiples))

    result = run_parallel_timing(C, 4, sys.stdout)
    assert(result == 42)

