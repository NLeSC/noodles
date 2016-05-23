import noodles
from noodles.run.runners import run_single


def test_empty_gather():
    d = noodles.gather()
    result = run_single(d)
    assert result == []
