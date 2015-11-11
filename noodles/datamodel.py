"""
    :author: Johan Hidding
    :description: Data model 2.0

    The data model works on a basis of delayed execution. The user calls
    decorated functions, building a workflow incrementally. Every node in the
    workflow can be thought of as a *promise* of a value.
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
