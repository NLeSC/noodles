from noodles import schedule, schedule_hint, gather
from noodles.datamodel import get_workflow
from noodles.coroutines import IOQueue, Connection
from noodles.run_common import run_job, Scheduler
from noodles.run_hybrid import hybrid_threaded_worker


@schedule_hint(1)
def f(x):
    return 2*x


@schedule_hint(2)
def g(x):
    return 3*x


@schedule
def h(x, y):
    return x + y


def simple_worker(tag):
    jobs = IOQueue()

    def get_result():
        source = jobs.source()

        for key, job in source:
            result = run_job(job)
            print("worker {0}: ".format(tag), job.foo.__name__,
                  job.bound_args, " --> ", result)
            yield (key, result)

    return Connection(get_result, jobs.sink)


def test_hints():
    def selector(hint):
        return hint[0]

    a = [f(x) for x in range(5)]
    b = [g(x) for x in range(5)]
    c = gather(*[h(x, y) for x in a for y in b])

    result = Scheduler().run(
        hybrid_threaded_worker(
            selector,
            {1: simple_worker(1), 2: simple_worker(2)}),
        get_workflow(c))

    print(result)

if __name__ == "__main__":
    test_hints()
