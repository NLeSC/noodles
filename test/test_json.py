from noodles import schedule, run
from noodles.data_node import importable, module_and_name
from noodles.data_json import workflow_to_json, json_to_workflow, Storable
import random


@schedule
def f(a, b):
    return a + b


@schedule
def g(a, b):
    return a - b


@schedule
def h(a, b):
    return a * b


def random_program(q=1.0, z=0.8):
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
    s = workflow_to_json(a._workflow, indent=2)
    b = json_to_workflow(s)
    ra = run(a)
    rb = run(b)
    assert ra.value == rb.value
    assert ra.second == rb.second


class B(Storable):
    def __init__(self, a, b):
        super(B, self).__init__()
        self.a = a
        self.b = b


@schedule
def sum_B(x):
    return x.a + x.b


def test_json_with_storable():
    b = B(2, 3)
    c = sum_B(b)
    d = B(4, c)
    e = sum_B(d)

    s = workflow_to_json(e._workflow, indent=2)
    f = json_to_workflow(s)

    re = run(e)
    rf = run(f)
    assert re == rf
