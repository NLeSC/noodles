from engine import *
from prototype import draw_workflow

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


w = sum(map(sqr, num_range(0, 10)))
draw_workflow("test.png", w)
print(run(w))
