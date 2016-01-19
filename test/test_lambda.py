from noodles import Scheduler, schedule, Lambda
from noodles.datamodel import get_workflow
from noodles.run_process import process_worker
from noodles.tutorial import accumulate


@schedule
def nmap(f, lst):
    return list(map(f, lst))


@schedule
def value(x):
    return x


def test_lambda():
    a = Lambda("lambda x: x**2")
    b = nmap(a, [0.1, 0.2, 0.3, 0.4, 0.5])
    c = accumulate(b)

    # result = run(c)
    result = Scheduler().run(process_worker(), get_workflow(c))
    assert result == 0.55
