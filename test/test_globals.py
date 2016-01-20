from noodles import schedule, Scheduler
from noodles.datamodel import get_workflow
from noodles.run_process import process_worker


@schedule
def init():
    global s
    s = "This global variable needs to be here!"
    return True


@schedule
def finish():
    return "Finish functino was run!"


@schedule
def checker():
    return s == "This global variable needs to be here!"


def test_globals():
    a = checker()
    result = Scheduler().run(process_worker(init=init, finish=finish), get_workflow(a))
    assert result

