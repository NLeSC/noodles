from engine import schedule

from prototype import draw_workflow

# define some simple functions

@schedule
def add(a, b):
    return a+b

@schedule
def min(a, b):
    return a-b

# run example program
#---------------------
r1 = add(42, 43)
r2 = add(41, r1)
r3 = min(r1, 44)
r4 = add(r2, r3)

# draw the execution graph
#-------------------------
draw_workflow("graph-example1.svg", r4)

