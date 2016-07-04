from .decorator import (schedule, PromisedObject)
# from copy import deepcopy


@schedule
def delay(value):
    return value


@schedule
def gather(*a):
    """
    Converts a list of workflows (i.e. :py:class:`PromisedObject`) to
    a workflow representing the promised list of values.

    Currently the :py:func:`from_call` function detects workflows
    only by their top type (using `isinstance`). If we have some
    deeper structure containing :py:class:`PromisedObject`, these are not
    recognised as workflow input and taken as literal values.

    This behaviour may change in the future, making this function
    `gather` obsolete.
    """
    return list(a)


def unpack(t, n):
    return (t[i] for i in range(n))


@schedule
def set_dict(obj, d):
    obj.__dict__ = d
    return obj


@schedule
def create_object(cls, members):
    obj = cls.__new__(cls)
    obj.__dict__ = members
    return obj


@schedule
def make_tuple(*args):
    return args


@schedule
def make_dict(*args):
    return dict(args)


@schedule
def make_list(*args):
    return list(args)


@schedule
def make_set(*args):
    return set(args)


def lift(obj, memo=None):
    if memo is None:
        memo = {}

    if isinstance(obj, (PromisedObject, str, int, float, complex)):
        return obj

    if id(obj) in memo:
        return memo[id(obj)]

    if hasattr(obj, '__lift__'):
        rv = obj.__lift__(memo)
        memo[id(obj)] = rv
        return rv

    actions = {
        list:  (lambda x: x, make_list),
        dict:  (lambda x: x.items(), make_dict),
        tuple: (lambda x: x, make_tuple),
        set:   (lambda x: x, make_set)
    }

    if obj.__class__ in actions:
        items, construct = actions[obj.__class__]
        tmp = [lift(a, memo) for a in items(obj)]
        if any(isinstance(a, PromisedObject) for a in tmp):
            rv = construct(*tmp)
            memo[id(obj)] = rv
            return rv
        else:
            memo[id(obj)] = obj
            return obj

    subclass = next(filter(
        lambda x: issubclass(obj.__class__, x),
        actions.keys()), None)

    if subclass:
        members = lift(obj.__dict__, memo)
        internal = lift(subclass(obj), memo)

        if isinstance(internal, PromisedObject):
            internal = schedule(obj.__class__)(internal)
            rv = set_dict(internal, members)
        elif isinstance(members, PromisedObject):
            rv = set_dict(obj.__class__(internal), members)
        else:
            rv = obj

        memo[id(obj)] = rv
        return rv

    members = lift(obj.__dict__, memo)
    if isinstance(members, PromisedObject):
        rv = create_object(obj.__class__, members)
    else:
        rv = obj

    memo[id(obj)] = rv
    return rv
