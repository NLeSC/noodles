"""
The basic types that define a workflow. All these types are serialisable through
JSON storage.
"""

from collections import namedtuple
from inspect import Parameter
from enum import Enum

ArgumentKind = Enum('ArgumentKind',
    ['regular', 'variadic', 'keyword'])

ArgumentAddress = namedtuple('ArgumentAddress',
    ['kind', 'name', 'key'])

Node = namedtuple('Node',
    ['module', 'name', 'arguments'])

Argument = namedtuple('Argument',
    ['address', 'value'])

Workflow = namedtuple('Workflow',
    ['root', 'nodes', 'links'])

Empty = Parameter.empty

def is_workflow(x):
    return isinstance(x, Workflow) or ('_workflow' in dir(x))

def get_workflow(x):
    if isinstance(x, Workflow):
        return x

    if '_workflow' in dir(x):
        return x._workflow

    return None
