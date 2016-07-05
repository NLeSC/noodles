import time

from noodles import schedule, schedule_hint, gather
from noodles.workflow import get_workflow
from noodles.run.connection import Connection
from noodles.run.scheduler import Scheduler
from noodles.run.worker import run_job
from noodles.run.hybrid import hybrid_coroutine_worker
from noodles.run.hybrid import run_hybrid

from noodles.run.haploid import haploid
from noodles.run.queue import (Queue)
from noodles.run.thread_pool import (thread_pool)
from noodles.run.worker import (worker)
from itertools import repeat


def single_worker():
    return Queue() >> worker


def threaded_worker(n_threads):
    return Queue() >> thread_pool(*repeat(worker, n_threads))


@schedule_hint(n=1)
def f(x):
    return 2*x


@schedule_hint(n=2)
def g(x):
    return 3*x


@schedule
def h(x, y):
    return x + y


def selector(job):
    if job.hints and 'n' in job.hints:
        return job.hints['n']
    else:
        return None


@schedule_hint(n=1)
def delayed(a, dt):
    time.sleep(dt)
    return a


@schedule
def sum(a, buildin_sum=sum):
    return buildin_sum(a)


def test_hybrid_threaded_runner_02():
    A = [delayed(1, 0.01) for i in range(8)]
    B = sum(gather(*A))

    start = time.time()
    assert run_hybrid(B, selector, {1: threaded_worker(8)}) == 8
    end = time.time()
    assert (end - start) < 0.05


def test_hybrid_threaded_runner_03():
    A = [delayed(1, 0.01) for i in range(8)]
    B = sum(gather(*A))

    start = time.time()
    assert run_hybrid(B, selector, {1: single_worker()}) == 8
    end = time.time()
    assert (end - start) > 0.08


def tic_worker(tic):
    jobs = Queue()

    @haploid('pull')
    def get_result():
        source = jobs.source()

        for key, job in source:
            tic()
            yield run_job(key, job)

    return Connection(get_result, jobs.sink)


def ticcer():
    a = 0

    def f():
        nonlocal a
        a += 1
        return a

    def g():
        nonlocal a
        return a

    return f, g


def test_hybrid_coroutine_runner_03():
    A1 = [f(i) for i in range(11)]
    A2 = [g(i) for i in range(7)]
    B = sum(gather(*(A1+A2)))

    tic1, c1 = ticcer()
    tic2, c2 = ticcer()

    result = Scheduler().run(
        hybrid_coroutine_worker(selector, {
            1: tic_worker(tic1), 2: tic_worker(tic2)}),
        get_workflow(B))

    assert c1() == 11
    assert c2() == 7
    assert result == 173
