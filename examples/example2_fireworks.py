from engine     import schedule, bind, run_fireworks
from prototype  import draw_workflow

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

# @schedule
# def runADF(jobinp, jobout):
#     xs = "module load adf\n$ADFBIN/adf  <{} > {}".format(jobinp, jobout) 
    
#     return BashScript(xs)

# a bit more complicated example
#-------------------------------
r1 = add(1, 1)
r2 = sub(3, r1)
r3 = add(r1,r2)

def foo(a, b, c):
    return mul(add(a, b), c)

multiples = [foo(i, r2, r1) for i in range(6)]

r5 = sum(bind(*multiples))

# draw_workflow("graph-example2.svg", r5)
print(r5)
answer = run_fireworks(r3, remote_db = "felipe@145.100.59.99" )

print("The answer is: {0}".format(answer))

