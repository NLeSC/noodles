"""The data model works on a basis of delayed execution. The user calls
decorated functions, building a workflow incrementally. Every node in the
workflow can be thought of as a *promise* of a value.
"""

from inspect import Parameter

from .data_types import (Workflow, Node, is_workflow, get_workflow, Empty,
                         ArgumentAddress, ArgumentKind)
from .data_arguments import (ref_argument, set_argument, format_address,
                             serialize_arguments)
from .data_node import FunctionNode, from_call
from .data_graph import invert_links
from .data_workflow import reset_workflow


__all__ = ['Workflow', 'Node',
           'FunctionNode', 'from_call', 'get_workflow',
           'is_workflow', 'get_workflow', 'Empty',
           'ArgumentAddress', 'ArgumentKind', 'reset_workflow',
           'insert_result', 'is_node_ready', 'invert_links']


def insert_result(node, address, value):
    """Runs `set_argument`, but checks first wether the data location is not
    already filled with some data. In any normal circumstance this checking
    is redundant, but if we don't give an error here the program would continue
    with unexpected results.
    """
    a = ref_argument(node.bound_args, address)
    if a != Parameter.empty:
        raise RuntimeError("Noodle panic. Argument {arg} in "
                           "{name} already given."
                           .format(arg=format_address(address),
                                   name=node.foo.__name__))

    set_argument(node.bound_args, address, value)


def is_node_ready(node):
    """Returns True if none of the argument holders contain any `Empty` object.
    """
    return all(ref_argument(node.bound_args, a) is not Parameter.empty
               for a in serialize_arguments(node.bound_args))
