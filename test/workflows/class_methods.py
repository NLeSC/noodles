from .workflow_factory import workflow_factory
from noodles import (
    schedule, has_scheduled_methods)


@has_scheduled_methods
class A:
    def __init__(self, x):
        super(A, self).__init__()
        self.x = x

    @schedule
    def __call__(self, y):
        return self.x * y


@workflow_factory(result=42)
def test_class_methods_00():
    a = A(7)
    return a(6)
