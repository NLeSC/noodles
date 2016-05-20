import noodles
from draw_workflow import draw_workflow
from noodles.tutorial import (add, mul, sub, accumulate)

def test_42():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    return accumulate(noodles.gather(*multiples))

draw_workflow("wf42.svg", test_42()._workflow)

