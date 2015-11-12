from noodles import *
import random, time

@schedule
def f(a, b):
    return a + b

@schedule
def g(a, b):
    return a - b

@schedule
def h(a, b):
    return a * b

def random_program(q = 1.0, z = 0.8):
    if random.random() > q:
        return random.random()
    else:
        return random.choice([f, g, h])(
            random_program(q*z),
            random_program(q*z))

def test_random_programs():
    for i in range(10):
        p1 = random_program()
        s = workflow_to_json(p1._workflow, indent=2)
        p2 = json_to_workflow(s)

        assert run(p1) == run(p2)

@schedule
class A:
    def __init__(self, value):
        self.value = value

    def multiply(self, factor):
        self.value *= factor
        return self

def test_json_with_class():
    a = A(5).multiply(10)
    a.second = 7
    s = workflow_to_json(a._workflow, indent = 2)
    b = json_to_workflow(s)
    ra = run(a)
    rb = run(b)
    assert ra.value == rb.value
    assert ra.second == rb.second
