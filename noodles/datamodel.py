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
    markers signifying that these arguments should be got at through the
    workflow.

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
from inspect import signature

from itertools import tee, filterfalse, chain, repeat, count

from .data_types import *
from .data_graph import *
from .data_arguments import *
from .data_json import *
from .data_node import *
from .data_workflow import *

def insert_result(node, address, value):
    """
    Runs `set_argument`, but checks first wether the data location is not
    already filled with some data. In any normal circumstance this checking
    is redundant, but if we don't give an error here the program would continue
    with unexpected results.
    """
    a = ref_argument(node.bound_args, address)
    if a != Parameter.empty:
        raise RuntimeError("Noodle panic. Argument {arg} in " \
                             "{name} already given."            \
                .format(arg=format_address(address), name=node.foo.__name__))

    set_argument(node.bound_args, address, value)

def is_node_ready(node):
    """
    Returns True if none of the argument holders contain any `Empty` object.
    """
    return all(ref_argument(node.bound_args, a) != Parameter.empty
        for a in serialize_arguments(node.bound_args))
