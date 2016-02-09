from noodles import (schedule, run_single)

@schedule
def double(x):
    return x['value'] * 2

@schedule
def add(x, y):
    return x + y

a = {'value': 4}
b = double(a)
a['value'] = 5
c = double(a)
d = add(b, c)

print(run_single(d))
