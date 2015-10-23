from engine import *

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


