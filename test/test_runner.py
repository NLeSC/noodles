from engine import *

@schedule
def value(a):
    return a

@schedule
def add(a, b):
    return a+b

@schedule
def sub(a, b):
    return a-b

@schedule
def mul(a, b):
    return a*b

@schedule
def sum(a, buildin_sum = sum):
    return buildin_sum(a)

def test_runner_01():
    A = value(1)
    B = value(1)
    C = add(A, B)

    assert run(C) == 2

def test_runner_02():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = sum(gather(*multiples))

    assert run(C) == 42

def test_parallel_runner_01():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = sum(gather(*multiples))

    assert run_parallel(C, 4) == 42

import time
from itertools import repeat

@schedule
def delayed(a, delay=1.0):
    time.sleep(delay)
    return a

def test_parallel_runner_02():
    A = repeat(delayed(1, 0.1), 4)
    B = sum(bind(*A))

    start = time.time()
    assert run_parallel(B, 4) == 4
    end = time.time()
    assert (end - start) < 0.2 # liberal upper limit for running time
