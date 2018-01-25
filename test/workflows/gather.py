import noodles
from noodles.tutorial import add
from .workflow_factory import workflow_factory


@workflow_factory(result=[])
def empty_gather():
    return noodles.gather()


@workflow_factory(result=list(range(0, 20, 2)))
def gather():
    return noodles.gather(*[add(x, x) for x in range(10)])


@workflow_factory(result={'a': 1, 'b': 2, 'c': 5})
def gather_dict():
    return noodles.gather_dict(a=1, b=add(1, 1), c=add(2, 3))


@workflow_factory(result=list(range(0, 30, 3)))
def test_gather_all():
    return noodles.gather_all(add(x, 2*x) for x in range(10))
