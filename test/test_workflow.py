import noodles
from noodles import run_single as run


@noodles.schedule
def named_arg(a, b, c):
    return [a, b, c]


@noodles.schedule
def variadic_arg(*args):
    return list(args)


@noodles.schedule
def keyword_arg(**kwargs):
    return list(kwargs.values())


def test_arguments():
    assert run(named_arg(1, 2, 3)) == [1, 2, 3]
    assert run(variadic_arg(1, 2, 3)) == [1, 2, 3]
    assert run(variadic_arg()) == []
    assert run(keyword_arg(a=1, b=2, c=3)) == [1, 2, 3]
