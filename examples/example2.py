from engine import schedule, bind
from prototype import draw_workflow

@schedule
def add(a, b):
    return a+b

@schedule
def min(a, b):
    return a-b

@schedule
def mul(a, b):
    return a*b

@schedule
def sum(a):
    b = 1
    for i in a:
        b += i
    return b

# a bit more complicated example
#-------------------------------
r1 = add(42, 43)
r2 = add(41, r1)

multiples = [mul(min(i, r2), r1) for i in range(10)]

r5 = sum(bind(*multiples))

draw_workflow("graph-example2.svg", r5)

