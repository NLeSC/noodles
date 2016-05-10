from noodles import (run_parallel)
from noodles.tutorial import (add)

def static_sum(values):
    if len(values) > 2:
        half = len(values) // 2
        return add(static_sum(values[:half]), static_sum(values[half:]))

    if len(values) == 2:
        return add(values[0], values[1])

    if len(values) == 1:
        return values[0]

result = run_parallel(static_sum(range(10)), 4)
print(result)

