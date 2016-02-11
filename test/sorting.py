import noodles
from numpy import random


@noodles.schedule
def random_number():
    return random.normal(0, 1)


def split(z):
    if len(z) == 0:
        return [], []
    if len(z) == 1:
        return z, []

    x, y = split(z[2:])
    return [z[0]] + x, [z[1]] + y

@noodles.schedule
def _m(x, xs, y, ys):
    if x <= y:
        return [x] + merge(xs, [y] + ys)
    else:
        return [y] + merge([x] + xs, ys)

def merge(x, y):
    if len(x) == 0:
        return y

    if len(y) == 0:
        return x

    return _m(x[0], x[1:], y[0], y[1:])

# @noodles.schedule
# def pivot_on_first(a, *rest):
#     if a > b:
#         return b, a
#     else
#         return a, b


def test_sort():
    a = [random_number() for i in range(10)]
    b = noodles.gather(*sorted(a))

    result = noodles.run_single(b)
    print(result)

    assert result == sorted(result)

