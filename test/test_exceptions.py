from nose.tools import raises
from noodles import (schedule, schedule_hint, run_single)


class MyException(Exception):
    def __init__(self, msg):
        super(MyException, self).__init__(msg)


@schedule
def raises_my_exception():
    raise MyException("Error!")


@raises(MyException)
def test_exception_00():
    wf = raises_my_exception()
    run_single(wf)


@schedule_hint(annotated=True)
def not_really_annotated():
    return 0


@raises(TypeError)
def test_exception_01():
    wf = not_really_annotated()
    run_single(wf)
