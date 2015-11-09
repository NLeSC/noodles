from collections import namedtuple
from inspect import Parameter
from enum import Enum

ArgumentKind = Enum('ArgumentKind',
    ['regular', 'variadic', 'keyword'])

ArgumentAddress = namedtuple('ArgumentAddress',
    ['kind', 'name', 'key'])

FunctionNode = namedtuple('FunctionNode',
    ['foo', 'bound_args'])

Node = namedtuple('Node',
    ['module', 'name', 'arguments'])

Argument = namedtuple('Argument',
    ['address', 'value'])

Workflow = namedtuple('Workflow',
    ['top', 'nodes', 'links'])

Empty = Parameter.empty
