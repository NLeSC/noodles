from noodles import *
from prototype import draw_workflow
@schedule_hint(1)
def f(x):
    return 2*x

@schedule_hint(2)
def g(x):
    return 3*x

@schedule
def h(x, y):
    return x + y

def single_worker_using(runner = run_job):
    jobs = IOQueue()

    def get_result():
        source = jobs.source()

        for key, job in source:
            yield (key, runner(job))

    return Connection(get_result, jobs.sink)

def rjp(n):
    def run_job_print(job):
        result = run_job(job)
        print("runner {n}: {f} {args} = {res}".format(
            n = n,
            f = job.foo.__name__,
            args = job.bound_args.args,
            res = result))
        return result

    return run_job_print

w0 = single_worker_using(rjp(0))
w1 = single_worker_using(rjp(1))
w2 = single_worker_using(rjp(2))

def selector(hints):
    if hints:
        return hints[0]
    else:
        return

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
