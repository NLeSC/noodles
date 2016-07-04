from noodles import schedule, run_parallel, run_single, gather, run_logging
import sys


@schedule
def sqr(a):
    return a*a


@schedule
def sum(a, buildin_sum=sum):
    return buildin_sum(a)


@schedule
def map(f, lst):
    return gather(*[f(x) for x in lst])


@schedule
def num_range(a, b):
    return range(a, b)


def test_higher_order():
    w = sum(map(sqr, num_range(0, 10)))
    assert run_parallel(w, 4) == 285


@schedule
def g(x):
    return f(x)


@schedule
def f(x):
    return x


class Display:
    def __call__(self, key, status, data, err_msg):
        print(status, data, err_msg)

    def error_handler(self, job, xcptn):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def test_single_node():
    with Display() as display:
        assert run_logging(g(5), 1, display) == 5
