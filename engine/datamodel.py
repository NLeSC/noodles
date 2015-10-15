"""
    @author: Johan Hidding
    @description: Data model 2.0
    
    The data model works on a basis of delayed execution. The user calls
    decorated functions, building a workflow incrementally. Every node in the
    workflow can be thought of as a _promise_ of a value. 
    
    ### Partial application
    In many cases the user will give a mixture of arguments to a function. Part
    may be ordinary values, part _promises_ from previous calls. We need to
    store the plain values at the node level, and the _promises_ in the shape
    of workflows should be merged to form a new workflow. In a sense this is a
    very fancy form of partial application. The original order of the arguments
    should be preserved in reconstructing the call to the function. To support
    this there are _splice_ functions, that replace items in the arguments with
    markers signifying that these arguments should be got at through the workflow.
    
    ### Memoization
    The user needs not 
    worry about the origin of the fulfillment of a _promise_. Most probably
    this value will be computed with some fancy package, but we don't like to
    compute things twice. A result can be cached by a process of memoization.
    Fireworks provides functionality to do this on the lowest level. On the
    high end we need to be aware of this. Functions should be _pure_. This means
    that with the same input, we are guaranteed the same answer.
"""

import inspect

from collections import namedtuple
from itertools import tee, filterfalse, chain, repeat, count
from enum import Enum

ArgumentType = Enum('ArgumentType', 
    ['regular', 'variadic', 'keyword'])

FunctionNode = namedtuple('FunctionNode', 
    ['foo', 'args', 'varargs', 'keywords'])

Workflow = namedtuple('Workflow', 
    ['top', 'nodes', 'links'])

# links: Mapping[NodeId, (NodeId, ArgumentType, [int|str])]

class EmptyType:
    def __str__(self):
        return u"\u2015"

Empty = EmptyType()

def is_workflow(x):
    return isinstance(x, Workflow)
    
def splice_list(pred, lst):
    """
    Splices a list based on predicate. Returns two lists where values have been
    replaced with `Empty` depending on the predicate's verdict.
    
    @param pred:
        predicate
    @type pred: Callable[[Any], bool]
    
    @param lst:
        input list
    @type lst: Sequence[Any]
    
    @returns:
        two lists, the first one containing items for which `pred` returns 
        `False`, the second one with items for which `pred` returns `True`.
    @rtype: Sequence[Any], Sequence[Any]
    """
    if lst == None: 
        return [], []
    return [Empty if pred(i) else i for i in lst], \
            [i if pred(i) else Empty for i in lst]
            
def splice_dict(pred, dct):
    """
    Splices a dictionary based on predicate. Returns two dictionaries with
    identical keys. The values are either the original value or `Empty`, based
    on the predicate's verdict.
    
    @param pred:
        predicate
    @type pred: Callable[[Any], bool]
    
    @param dct:
        dictionary
    @type dct: Mapping[KeyType, Any]
    
    @returns:
        two dicts, the first one containing items for which `pred` returns 
        `False`, the second one with items for which `pred` returns `True`.
    @rtype: Mapping[KeyType, Any], Mapping[KeyType, Any]
    """
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
                      
                  zip(count(),
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

def _all_valid(links):
    """
    Iterates over all links, forgetting emtpy registers.
    """
    for k, v in links.items():
        for i in v:
            yield k, i

def invert_links(links):
    """
    Inverts the call-graph to get a dependency graph. Possibly slow, 
    short version.
    
    @param links:
        forward links of a call-graph.
    @type links: Mapping[NodeId, Set[(NodeId, ArgumentType, [int|str]])]
    
    @returns:
        inverted graph, giving dependency of jobs.
    @rtype: Mapping[NodeId, Mapping[(ArgumentType, [int|str]), NodeId]]
    """
    return dict((node, dict(((arg_type, kw), src) 
                    for src, (tgt, arg_type, kw) in _all_valid(links)
                    if tgt == node)) 
                for node in links)

def is_node_ready(node):
    """
    Returns True if none of the argument holders contain any `Empty` object.
    """
    return all(a != Empty for a in chain(
        node.args, node.varargs, node.keywords.values()))

