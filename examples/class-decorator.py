from noodles import *
from prototype import draw_workflow

@schedule
class A:
    def __init__(self, value):
        self.value = value

    def multiply(self, factor):
        self.value *= factor
        return self

a = A(5).multiply(10)
a.second = 7

draw_workflow("oop-wf.svg", a)
result = run(a)
print(result.value, result.second)
