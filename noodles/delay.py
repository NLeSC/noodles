from copy import deepcopy
from .workflow import get_workflow


class DelayedWorkflow(object):
    def __init__(self, obj):
        self.data = get_workflow(obj)

    def __deepcopy__(self, memo):
        # return DelayedWorkflow(self.data)
        return DelayedWorkflow(deepcopy(self.data, memo))


def delay(obj):
    return DelayedWorkflow(obj)


def force(dw):
    if isinstance(dw, DelayedWorkflow):
        return dw.data
    else:
        return dw

