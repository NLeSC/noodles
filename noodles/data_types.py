"""
The basic types that define a workflow. All these types are serialisable
through JSON storage.
"""

from collections import namedtuple
from inspect import Parameter
from enum import Enum

ArgumentKind = Enum(
    'ArgumentKind',
    ['regular', 'variadic', 'keyword'])

ArgumentAddress = namedtuple(
    'ArgumentAddress',
    ['kind', 'name', 'key'])

Node = namedtuple(
    'Node',
    ['function', 'arguments', 'hints'])

Argument = namedtuple(
    'Argument',
    ['address', 'value'])


class Workflow(namedtuple('Workflow', ['root', 'nodes', 'links'])):
    """
    The workflow data container.

    .. py:attribute:: root

        A reference to the root node in the graph.

    .. py:attribute:: nodes

        A `dict` listing the nodes in the graph. We use a `dict` only to have
        a persistent object reference.

    .. py:attribute:: links

        A `dict` giving a `set` of links from each node.
    """

Empty = Parameter.empty


def is_workflow(x):
    return isinstance(x, Workflow) or ('_workflow' in dir(x))


def get_workflow(x):
    if isinstance(x, Workflow):
        return x

    if '_workflow' in dir(x):
        return x._workflow

    return None
