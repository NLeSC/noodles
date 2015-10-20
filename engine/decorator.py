from inspect import getargspec, signature
from itertools import tee, filterfalse, repeat, chain

from lib import *

from .datamodel import FunctionNode, Workflow, merge_workflow   
    
def schedule(f):
    """
    Function decorator. The function will return a workflow in stead of
    being applied immediately. This workflow can then be passed to a job
    scheduler in order to be run on any architecture supporting the current
    python environment.    
    """
    def wrapped(*args, **kwargs):
        bound_args = signature(f).bind(*args, **kwargs)
        bound_args.apply_defaults()
        return merge_workflow(f, bound_args)        

    wrapped.__doc__ = f.__doc__
    return wrapped


def bind(*a):
    def binder(*args):
        return list(args)
    
    bound_args = signature(binder).bind(*a)
    return merge_workflow(binder, bound_args)

