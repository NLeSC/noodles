from engine import schedule, bind, run
from prototype import draw_workflow

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
def sum(a):
    b = 0
    for i in a:
        b += i
    return b

# a bit more complicated example
#-------------------------------
r1 = add(1, 1)
r2 = sub(3, r1)

multiples = [mul(add(i, r2), r1) for i in range(6)]

r5 = sum(bind(*multiples))

draw_workflow("graph-example2.svg", r5)
answer = run(r5)

print("The answer is: {0}".format(answer))

