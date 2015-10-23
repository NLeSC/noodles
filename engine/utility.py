from inspect import signature
from .datamodel import merge_workflow

def bind(*a):
    def binder(*args):
        return list(args)
    
    bound_args = signature(binder).bind(*a)
    return merge_workflow(binder, bound_args)


