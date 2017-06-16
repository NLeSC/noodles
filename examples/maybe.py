from noodles import (schedule, maybe, run_single)


@schedule
@maybe
def inv(x):
    return 1/x


@schedule
@maybe
def add(**args):
    return sum(args.values())


if __name__ == "__main__":
    wf = add(a=inv(0), b=inv(0))
    result = run_single(wf)
    print(result)
