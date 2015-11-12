from noodles import *
from nose.tools import raises

@schedule
class A:
    def __init__(self, value):
        self.value = value

    def multiply(self, factor):
        self.value *= factor
        return self

def test_class_decorator():
    a = A(5).multiply(10)
    a.second = 7
    result = run(a)
    assert result.value == 50
    assert result.second == 7

def f(x):
    return x

def test_unwrap():
    assert f == unwrap(schedule(f))
    assert f == unwrap(f)

@raises(AttributeError)
def test_class_decorator2():
    a = A(6).multiply(7)
    b = a.divide(0)
    result = run(b)
    print(dir(result))
