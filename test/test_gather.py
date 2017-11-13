import noodles
from noodles.run.runners import run_single
from noodles.tutorial import add


def test_empty_gather():
    d = noodles.gather()
    result = run_single(d)
    assert result == []


def test_gather():
    d = noodles.gather(*[add(x, x) for x in range(10)])
    result = run_single(d)
    assert result == list(range(0, 20, 2))


def test_gather_dict():
    d = noodles.gather_dict(a=1, b=add(1, 1), c=add(2, 3))
    result = run_single(d)
    assert result == {'a': 1, 'b': 2, 'c': 5}


def test_gather_all():
    d = noodles.gather_all(add(x, 2*x) for x in range(10))
    result = run_single(d)
    assert result == list(range(0, 30, 3))
