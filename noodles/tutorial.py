from . import schedule, schedule_hint


@schedule
def add(x, y):
    return x + y


@schedule_hint(display="{a} + {b}", confirm=True)
def log_add(a, b):
    return a + b


@schedule
def sub(x, y):
    return x - y


@schedule
def mul(x, y):
    return x*y


@schedule
def accumulate(lst, start=0):
    return sum(lst, start)
