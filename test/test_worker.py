from noodles import schedule, Scheduler, gather
from noodles.datamodel import get_workflow
from noodles.run_process import process_worker


@schedule
def f(x, y):
    return x + y


@schedule
def sum(lst, acc=sum):
    return acc(lst)


def test_worker():
    a = [f(i, j) for i in range(5) for j in range(5)]
    b = sum(gather(*a))

    result = Scheduler().run(process_worker(), get_workflow(b))
    assert result == 100
