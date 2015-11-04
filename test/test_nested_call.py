from engine import *

@schedule
def sqr(a):
    return a*a

@schedule
def sum(a, buildin_sum = sum):
    return buildin_sum(a)

@schedule
def map(f, lst):
    return bind(*[f(x) for x in lst])

@schedule
def num_range(a, b):
    return range(a, b)

def test_higher_order():
    w = sum(map(sqr, num_range(0, 10)))
    assert run_parallel(w, 4) == 285
