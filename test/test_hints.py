from noodles import schedule, schedule_hint, gather
from noodles.run_local import single_worker, threaded_worker
from noodles.run_hybrid import run_hybrid

import time


@schedule_hint(1)
def f(x):
    return 2*x


@schedule_hint(2)
def g(x):
    return 3*x


@schedule
def h(x, y):
    return x + y


def selector(hints):
    if hints:
        return hints[0]
    else:
        return


@schedule_hint(1)
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
    assert (end - start) < 0.02


def test_hybrid_threaded_runner_03():
    A = [delayed(1, 0.01) for i in range(8)]
    B = sum(gather(*A))

    start = time.time()
    assert run_hybrid(B, selector, {1: single_worker()}) == 8
    end = time.time()
    assert (end - start) > 0.08


# def test_hints():
#     a = [f(x) for x in range(5)]
#     b = [g(x) for x in range(5)]
#     c = gather(*[h(x, y) for x in a for y in b])
#
#     draw_workflow('test.png', get_workflow(c))
#     result = Scheduler().run(
# #        threaded_worker(4),
#         hybrid_worker(selector, {1: w1, 2: w2}, w0),
#         get_workflow(c))
#
#     print(result)
