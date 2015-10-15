"""
    @author: Johan Hidding
    @description: Data model 2.0
"""

import inspect

from collections import namedtuple
from itertools import tee, filterfalse, chain, repeat
from enum import Enum

ArgumentType = Enum('ArgumentType', 
    ['regular', 'variadic', 'keyword'])

FunctionNode = namedtuple('FunctionNode', 
    ['foo', 'args', 'varargs', 'keywords'])

Workflow = namedtuple('Workflow', 
    ['top', 'nodes', 'links'])

class EmptyType:
    def __str__(self):
        return u"\u2015"

Empty = EmptyType()

def is_workflow(x):
    return isinstance(x, Workflow)
    
def splice_list(pred, lst):
    if lst == None: 
        return [], []
    return [Empty if pred(i) else i for i in lst], \
            [i if pred(i) else Empty for i in lst]
            
def splice_dict(pred, dct):
    if dct == None:
        return {}, {}
    return dict((k, Empty if pred(v) else v) for k, v in dct.items()), \
            dict((k, v if pred(v) else Empty) for k, v in dct.items())

def merge_workflow(f, args, vargs, kwargs):
    """
    Arguments: the new root node (to be added) and a list of graphs.
    Returns: a new graph with the original list of graphs merged into
    one, detecting identical nodes by their Python object id.
    
    Typically the node is a function to be called, and the list of graphs
    represents the computations that had to be performed to get the
    arguments for the function application.
    """
    
    fixed_args,   link_args   = splice_list(is_workflow, args)
    fixed_vargs,  link_vargs  = splice_list(is_workflow, vargs)
    fixed_kwargs, link_kwargs = splice_dict(is_workflow, kwargs)
    
    node = FunctionNode(f, fixed_args, fixed_vargs, fixed_kwargs)
    arg_spec = inspect.getargspec(f)
    
    idx = id(node)
    nodes = {idx: node}
    links = {idx: set()}
        
    items = chain(zip(arg_spec.args,
                      link_args,            
                      repeat(ArgumentType.regular)),
                      
                  zip(repeat('*'),
                      link_vargs,
                      repeat(ArgumentType.variadic)),
                      
                  zip(link_kwargs.keys(), 
                      link_kwargs.values(),
                      repeat(ArgumentType.keyword)))
        
    for name, workflow, argument_type in items:
        if workflow == Empty:
            continue
        
        for n in workflow.nodes:
            if n not in nodes:
                nodes[n] = workflow.nodes[n]
                links[n] = set()
            
            links[n].update(workflow.links[n])
            
        links[workflow.top].add((idx, argument_type, name))
                            
    return Workflow(id(node), nodes, links)

