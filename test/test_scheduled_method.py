from noodles import (schedule, Scheduler, has_scheduled_methods, serial)
from noodles.serial import (Registry, AsDict)
from noodles.workflow import get_workflow
from noodles.run.process import process_worker


def registry():
    reg = Registry(parent=serial.base())
    reg[A] = AsDict(A)
    return reg


@has_scheduled_methods
class A:
    def __init__(self, a):
        super(A, self).__init__()
        self.a = a

    @schedule
    def mul(self, b):
        return self.a * b


def test_sched_meth():
    a = A(5)
    b = a.mul(5)
    result = Scheduler().run(process_worker(registry), get_workflow(b))
    assert result == 25
