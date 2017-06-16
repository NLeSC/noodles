from noodles import schedule, run_single, run_parallel, gather, result
import time


@schedule
def value(a):
    return a


@schedule
def add(a, b):
    return a+b


@schedule
def sub(a, b):
    return a-b


@schedule
def mul(a, b):
    return a*b


@schedule
def sum(a, buildin_sum=sum):
    return buildin_sum(a)


def test_runner_01():
    A = value(1)
    B = value(1)
    C = add(A, B)

    assert run_single(C) == 2
    assert result(A) == 1
    assert result(B) == 1


def test_runner_02():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = sum(gather(*multiples))

    assert run_single(C) == 42
    assert result(C) == 42
    assert result(A) == 2


def test_parallel_runner_01():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = sum(gather(*multiples))

    assert run_parallel(C, 4) == 42


@schedule
def delayed(a, delay=1.0):
    time.sleep(delay)
    return a


def test_parallel_runner_02():
    A = [delayed(1, 0.01) for i in range(100)]
    B = sum(gather(*A))

    start = time.time()
    assert run_parallel(B, 4) == 100
    end = time.time()
    # print(end-start)
    assert (end - start) < 0.4   # liberal upper limit for running time
