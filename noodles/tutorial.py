from . import schedule


@schedule
def add(x, y):
    return x + y


@schedule
def sub(x, y):
    return x - y


@schedule
def mul(x, y):
    return x*y


@schedule
def accumulate(lst, start=0):
    return sum(lst, start)
