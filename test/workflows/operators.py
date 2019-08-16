import noodles
# import numpy as np

from .workflow_factory import workflow_factory


@noodles.schedule
def promise(x):
    return x


@workflow_factory(result=42)
def answer():
    return promise(6) * promise(7)
