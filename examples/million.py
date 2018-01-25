import noodles
from noodles.run.local import run_single


@noodles.schedule
def large_sum(lst, acc=0):
    if len(lst) < 1000:
        return acc + sum(lst)
    else:
        return large_sum(lst[1000:], acc+sum(lst[:1000]))


a = large_sum(range(1000000))
result = run_single(a)

print("sum of 1 .. 1000000 is ", result)
