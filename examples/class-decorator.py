from noodles import *
from prototype import draw_workflow

@schedule
def sqr(x):
    return x*x

@schedule
def divide(x, y):
    return x/y

@schedule
def mul(x, y):
    return x*y

@schedule
class A:
    def __init__(self, value):
        self.x = value

    def multiply(self, factor):
        self.x *= factor
        return self

    @property
    def attr(self):
        return sqr(self.__attr)

    def mul_attr(self, factor = 1):
        return mul(self.__attr, factor)

    @attr.setter
    def attr(self, x):
        self.__attr = divide(x, 2)

@schedule
class B:
    pass

a = A(5).multiply(10)
a.second = 7
a.attr = 1.0

b = B()
b.x = a.x
b.second = a.second
b.attr = a.attr

draw_workflow("oop-wf.svg", b)
result = run(b)

print(result.x, result.second, result.attr)
