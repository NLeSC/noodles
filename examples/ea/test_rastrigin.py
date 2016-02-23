from noodles import run_single
from ea.rastrigin import Rastrigin
import numpy as np

def test_rastrigin_zero():
    rastrigin = Rastrigin(10)
    values = np.zeros(10)
    answer = run_single(rastrigin.evaluate(values))

    print("For values {:s} found answer: {:s}", values,answer)
    assert answer == 0

def test_rastrigin_non_zero():
    rastrigin = Rastrigin(10)
    values = np.random.random(10)
    answer = run_single(rastrigin.evaluate(values))

    print("For values {:s} found answer: {:s}", values,answer)
    assert answer != 0
