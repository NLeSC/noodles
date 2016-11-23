from collections import namedtuple
from enum import Enum
from itertools import repeat
from inspect import Parameter, signature

Empty = Parameter.empty

ArgumentKind = Enum(
    'ArgumentKind',
    ['regular', 'variadic', 'keyword'])

ArgumentAddress = namedtuple(
    'ArgumentAddress',
    ['kind', 'name', 'key'])

Argument = namedtuple(
    'Argument',
    ['address', 'value'])


def serialize_arguments(bound_args):
    """
    Generator that takes the bound_args output of signature().bind and iterates
    over all the arguments, returning reproducable addresses of each
    argument.

    An address is stored in an `ArgumentAddress` object (a
    named tuple), containing the kind of argument
    (regular, variadic or keyword),
    the name of the argument, and, if not a regular argument, a key.
    In the case of a variadic argument this is an integer index into the
    variadic arguments list, in the case of a keyword argument it is a
    string. For regular arguments the key is set to `None`.

    :param bound_args:
        Bound arguments structure, as described in the documentation of the
        `inspect` module.
    :type bound_args: BoundArguments

    :returns:
        Generates (kind, name, key)-tuples representing an address into the
        argument structure.
    :rtype: Iterator[ArgumentAddress]
    """
    for p in bound_args.signature.parameters.values():
        if p.kind == Parameter.VAR_POSITIONAL:
            for i, _ in enumerate(bound_args.arguments[p.name]):
                yield ArgumentAddress(ArgumentKind.variadic, p.name, i)
            continue

        if p.kind == Parameter.VAR_KEYWORD:
            for k in bound_args.arguments[p.name].keys():
                yield ArgumentAddress(ArgumentKind.keyword, p.name, k)
            continue

        yield ArgumentAddress(ArgumentKind.regular, p.name, None)


def ref_argument(bound_args, address):
    """
    Taking a bound_args object, and an ArgumentAddress, retrieves the data
    currently stored in bound_args for this particular address.
    """
    if address.kind == ArgumentKind.regular:
        return bound_args.arguments[address.name]

    return bound_args.arguments[address.name][address.key]


def set_argument(bound_args, address, value):
    """
    Taking a bound_args object, and  an ArgumentAddress and a value,
    sets the value pointed to by the address to `value`.
    """
    if address.kind == ArgumentKind.regular:
        bound_args.arguments[address.name] = value
        return

    if address.kind == ArgumentKind.variadic:
        if address.name not in bound_args.arguments:
            bound_args.arguments[address.name] = []

        l = len(bound_args.arguments[address.name])
        if address.key >= l:
            bound_args.arguments[address.name].extend(
                repeat(Empty, address.key - l + 1))

    if address.kind == ArgumentKind.keyword:
        if address.name not in bound_args.arguments:
            bound_args.arguments[address.name] = {}

    bound_args.arguments[address.name][address.key] = value


def format_address(address):
    """
    Formats an ArgumentAddress for human reading.
    """
    if address.kind == ArgumentKind.regular:
        return address.name

    return "{0}[{1}]".format(address.name, address.key)


def get_arguments(bound_args):
    return [(address, ref_argument(bound_args, address))
            for address in serialize_arguments(bound_args)
            if ref_argument(bound_args, address) is not Empty]


def bind_arguments(f, arguments):
    bound_args = signature(f).bind_partial()

    variadic = next((x.name
                     for x in bound_args.signature.parameters.values()
                     if x.kind == Parameter.VAR_POSITIONAL), None)

    if variadic:
        bound_args.arguments[variadic] = []

    keyword = next((x.name
                    for x in bound_args.signature.parameters.values()
                    if x.kind == Parameter.VAR_KEYWORD), None)

    if keyword:
        bound_args.arguments[keyword] = {}

    for address, value in arguments:
        set_argument(bound_args, address, value)

    return bound_args
