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
from inspect import signature, Parameter

from collections import namedtuple
from itertools import tee, filterfalse, chain, repeat, count
from enum import Enum

ArgumentKind = Enum('ArgumentKind', 
    ['regular', 'variadic', 'keyword'])

ArgumentAddress = namedtuple('ArgumentAddress',
    ['kind', 'name', 'key'])

FunctionNode = namedtuple('FunctionNode',
    ['foo', 'bound_args'])

Workflow = namedtuple('Workflow', 
    ['top', 'nodes', 'links'])

Empty = Parameter.empty
# links: Mapping[NodeId, (NodeId, ArgumentAddress)]


def is_workflow(x):
    return isinstance(x, Workflow) or ('_workflow' in dir(x))

def get_workflow(x):
    if isinstance(x, Workflow):
        return x
        
    if '_workflow' in dir(x):
        return x._workflow
    
    return None

def serialize_arguments(bound_args):
    for p in bound_args.signature.parameters.values():
        if p.kind == Parameter.VAR_POSITIONAL:
            for i, v in enumerate(bound_args.arguments[p.name]):
                yield ArgumentAddress(ArgumentKind.variadic, p.name, i)
            continue
        
        if p.kind == Parameter.VAR_KEYWORD:
            for k, v in bound_args.arguments[p.name].items():
                yield ArgumentAddress(ArgumentKind.keyword, p.name, k)
            continue
        
        yield ArgumentAddress(ArgumentKind.regular, p.name, None)

def ref_argument(bound_args, address):
    if address.kind == ArgumentKind.regular:
        return bound_args.arguments[address.name]
            
    return bound_args.arguments[address.name][address.key]

def set_argument(bound_args, address, value):
    if address.kind == ArgumentKind.regular:
        bound_args.arguments[address.name] = value
        return
            
    bound_args.arguments[address.name][address.key] = value

def format_address(address):
    if address.kind == ArgumentKind.regular:
        return address.name
        
    return "{0}[{1}]".format(address.name, address.key)

def insert_result(node, address, value):
    a = ref_argument(node.bound_args, address)
    if a != Parameter.empty:
        raise RuntimeError("Noodle panic. Argument {arg} in " \
                             "{name} already given."            \
                .format(arg=format_address(address), name=node.foo.__name__))
    
    set_argument(node.bound_args, address, value)
  
def merge_workflow(f, bound_args):    
    variadic = next((x.name for x in bound_args.signature.parameters.values()
        if x.kind == Parameter.VAR_POSITIONAL), None)

    # *UGLY HACK*
    # the BoundArguments class uses a tuple to store the
    # variadic arguments. Since we need to modify them,
    # we have to replace the tuple with a list. This works, for now...
    if variadic:
        bound_args.arguments[variadic] = list(bound_args.arguments[variadic])
    
    node = FunctionNode(f, bound_args)
    
    idx = id(node)
    nodes = {idx: node}
    links = {idx: set()}

    for address in serialize_arguments(bound_args):
        workflow = get_workflow(
            ref_argument(bound_args, address))
        
        if not workflow:
            continue
        
        set_argument(bound_args, address, Parameter.empty)
        for n in workflow.nodes:
            if n not in nodes:
                nodes[n] = workflow.nodes[n]
                links[n] = set()
            
            links[n].update(workflow.links[n])
            
        links[workflow.top].add((idx, address))
        
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
    return dict((node, dict((address, src) 
                    for src, (tgt, address) in _all_valid(links)
                    if tgt == node))
                for node in links)

def is_node_ready(node):
    """
    Returns True if none of the argument holders contain any `Empty` object.
    """
    return all(ref_argument(node.bound_args, a) != Parameter.empty 
        for a in serialize_arguments(node.bound_args))

