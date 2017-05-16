from noodles import schedule, gather, serial, run_logging
from noodles.run.run_with_prov import run_parallel_opt
from noodles.display import (DumbDisplay)

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
def my_sum(a, buildin_sum=sum):
    return buildin_sum(a)


# a bit more complicated example
# -------------------------------
r1 = add(1, 1)
r2 = sub(3, r1)


def foo(a, b, c):
    return mul(add(a, b), c)


multiples = [foo(i, r2, r1) for i in range(6)]

r5 = my_sum(gather(*multiples))

# draw_workflow("graph-example2.svg", r5)

with DumbDisplay() as display:
    answer = run_logging(r5, 4, display)
    #answer = run_parallel_opt(
    #        r5, 4, serial.base, "cache.json",
    #        display=display, cache_all=True)

print("The answer is: {0}".format(answer))
