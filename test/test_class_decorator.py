from noodles import schedule, run_single, unwrap, run_process, Storable
from noodles import serial
from pytest import raises


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
def make_object(cls, *args, **kwargs):
    return cls(*args, **kwargs)


class A(Storable):
    def __init__(self, value):
        # super(A, self).__init__()
        self.value = value
        self.m_attr = 0

    @property
    def attr(self):
        return sqr(self.m_attr)

    def mul_attr(self, factor=1):
        return mul(self.m_attr, factor)

    @attr.setter
    def attr(self, x):
        self.m_attr = divide(x, 2)

    def multiply(self, factor):
        self.value *= factor
        return self


class B:
    pass


def test_class_decorator():
    a = make_object(A, 5).multiply(10)
    a.second = 7
    result = run_single(a)
    assert result.value == 50
    assert result.second == 7


def registry():
    return serial.base()


def test_class_decorator_process():
    a = make_object(A, 5).multiply(10)
    a.second = 7
    result = run_process(
        a, n_processes=1, registry=registry)
    assert result.value == 50
    assert result.second == 7


def test_class_property():
    a = make_object(A, 10)
    a.attr = 1.0

    b = make_object(B)
    b.first = a.attr
    b.second = a.mul_attr(3)

    result = run_single(b)
    assert result.first == 0.25
    assert result.second == 1.5

# @schedule
# def should_not_run():
#     raise RuntimeError
#
# def test_setget_optimisation1():
#     a = B()
#     a.r = 5
#     a.s = should_not_run()
#
#     b = B()
#     b.t = a.r
#
#     result = run(b)
#     assert result.t == 5
#
# @raises(RuntimeError)
# def test_setget_optimisation2():
#     a = B()
#     a.s = should_not_run()
#     a.r = 5
#
#     b = B()
#     b.t = a.r
#
#     result = run(b)
#     assert result.t == 5


def f(x):
    return x


def test_unwrap():
    assert f == unwrap(schedule(f))
    assert f == unwrap(f)


def test_class_decorator2():
    with raises(AttributeError):
        a = make_object(A, 6).multiply(7)
        b = a.divide(0)
        result = run_single(b)
        print(dir(result))
