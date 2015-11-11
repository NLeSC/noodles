from noodles import schedule

from prototype import draw_workflow

# define some simple functions

@schedule
def f(a, b):
    return a+b

@schedule
def g(a, b):
    return a-b

@schedule
def h(a, b):
    return a*b

# run example program
#---------------------
u = f(5, 4)
v = g(u, 3)
w = g(u, 2)
x = h(v, w)

# draw the execution graph
#-------------------------
draw_workflow("callgraph.png", x)
