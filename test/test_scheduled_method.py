from noodles import (schedule, Scheduler, Storable, has_scheduled_methods,
                     Registry, serial, AsDict)
from noodles.datamodel import get_workflow
from noodles.run_process import process_worker


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
