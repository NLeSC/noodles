from .workflow_factory import workflow_factory
import noodles


class A(dict):
    pass


@noodles.schedule
def f(a):
    a['value'] = 5
    return a


@workflow_factory(
    assertions=[
        lambda r: isinstance(r, A),
        lambda r: r['value'] == 5])
def test_dict_like():
    a = A()
    return f(a)
