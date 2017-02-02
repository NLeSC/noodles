from pytest import raises
from noodles import (schedule, schedule_hint, run_single)


class MyException(Exception):
    def __init__(self, msg):
        super(MyException, self).__init__(msg)


@schedule
def raises_my_exception():
    raise MyException("Error!")


def test_exception_00():
    with raises(MyException):
        wf = raises_my_exception()
        run_single(wf)


@schedule_hint(annotated=True)
def not_really_annotated():
    return 0


def test_exception_01():
    with raises(TypeError):
        wf = not_really_annotated()
        run_single(wf)
