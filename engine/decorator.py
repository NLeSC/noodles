from inspect import signature
from itertools import tee, filterfalse, repeat, chain
from functools import wraps

from lib import *

from .datamodel import FunctionNode, Workflow, merge_workflow, get_workflow

def schedule(f):
    """
    Function decorator. The function will return a workflow in stead of
    being applied immediately. This workflow can then be passed to a job
    scheduler in order to be run on any architecture supporting the current
    python environment.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        bound_args = signature(f).bind(*args, **kwargs)
        bound_args.apply_defaults()
        return PromisedObject(merge_workflow(f, bound_args))

    return wrapped

def unwrap(f):
    try:
        return f.__wrapped__
    except AttributeError:
        return f

@schedule
def _getattr(obj, attr):
    if not (attr in dir(obj)):
        raise AttributeError("{0} not in {1}.".format(attr, obj))

    return obj.__getattribute__(attr)

@schedule
def _setattr(obj, attr, value):
    obj.__setattr__(attr, value)
    return obj

@schedule
def _do_call(obj, *args, **kwargs):
    return obj(*args, **kwargs)

class PromisedObject:
    def __init__(self, workflow):
        self._workflow = workflow

    def __call__(self, *args, **kwargs):
        return _do_call(self._workflow, *args, **kwargs)

    def __getattr__(self, attr):
        if attr[0] == '_':
            return self.__dict__[attr]

        return _getattr(self._workflow, attr)

    def __setattr__(self, attr, value):
        if attr[0] == '_':
            self.__dict__[attr] = value
            return

        self._workflow = get_workflow(_setattr(self._workflow, attr, value))
