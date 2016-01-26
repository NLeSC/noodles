from noodles import schedule, run_process
import sys


class A(object):
    def __init__(self, a):
        self.a = a

    @classmethod
    def from_dict(cls, a):
        return cls(a)

    def as_dict(self):
        print("Running as_dict!", file=sys.stderr)
        return {'a': self.a}


@schedule
def g(a):
    return A(a)

@schedule
def f(a):
    return a.a * 5


def test_autostorable():
    a = g(7)
    b = f(a)
    result = run_process(b, n_processes=1, verbose=True)
    assert result == 35
