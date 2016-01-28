from noodles import (
    schedule, has_scheduled_methods, run_single,
    run_process, serial)


def registry():
    return serial.pickle() + serial.base()


@has_scheduled_methods
class A:
    def __init__(self, x):
        super(A, self).__init__()
        self.x = x

    @schedule
    def __call__(self, y):
        return self.x * y


def test_class_methods_00():
    a = A(7)
    b = a(6)

    result = run_single(b)
    assert result == 42


def test_class_methods_01():
    a = A(7)
    b = a(6)

    result = run_process(b, 1, registry)
    assert result == 42
