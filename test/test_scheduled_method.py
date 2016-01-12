from noodles import schedule, Scheduler, Storable, has_scheduled_methods
from noodles.datamodel import get_workflow
from noodles.run_process import process_worker


@has_scheduled_methods
class A(Storable):
    def __init__(self, a):
        super(A, self).__init__()
        self.a = a

    @schedule
    def mul(self, b):
        return self.a * b


def test_sched_meth():
    a = A(5)
    b = a.mul(5)
    result = Scheduler().run(process_worker(), get_workflow(b))
    assert result == 25
