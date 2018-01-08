from .workflow_factory import workflow_factory
import noodles


@noodles.schedule
def writes_to_stdout():
    print("Hello Noodles!")
    return 42


@workflow_factory(
    result=42,
    requires=['remote'])
def capture_output():
    return writes_to_stdout()
