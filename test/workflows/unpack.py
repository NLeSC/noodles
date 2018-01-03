from .workflow_factory import workflow_factory
import noodles
from noodles.tutorial import add


@workflow_factory(raises=TypeError)
def unguarded_iteration():
    a = noodles.delay((1, 2, 3))
    b, c, d = a
    return noodles.gather(d, c, b)


@noodles.schedule
def f():
    return 1, 2, 3


@workflow_factory(result=6)
def unpack():
    a, b, c = noodles.unpack(f(), 3)
    return add(a, add(b, c))
