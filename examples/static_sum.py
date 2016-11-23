from noodles import (run_parallel, schedule)
from noodles.tutorial import (add)

# import numpy as np


def static_sum(values, limit_n=1000):
    """Example of static sum routine."""
    if len(values) < limit_n:
        return sum(values)

    else:
        half = len(values) // 2
        return add(
                static_sum(values[:half], limit_n),
                static_sum(values[half:], limit_n))


@schedule
def dynamic_sum(values, limit_n=1000, acc=0, depth=4):
    """Example of dynamic sum."""
    if len(values) < limit_n:
        return acc + sum(values)

    if depth > 0:
        half = len(values) // 2
        return add(
            dynamic_sum(values[:half], limit_n, acc, depth=depth-1),
            dynamic_sum(values[half:], limit_n, 0, depth=depth-1))

    return dynamic_sum(values[limit_n:], limit_n,
                       acc + sum(values[:limit_n]), depth)


result = run_parallel(dynamic_sum(range(1000000000), 1000000), 4)
print(result)
