import noodles
from noodles.run.local import run_single

def test_gather():
    d = noodles.gather()
    result = run_single(d)
    assert result == []
