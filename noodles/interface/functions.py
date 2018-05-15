"""
.. default-domain:: py
"""

from .decorator import (schedule, PromisedObject)
# from .maybe import (maybe)
# from copy import deepcopy
# from ..serial.reasonable import Reasonable


class Ref:
    """The Ref object circumvents deep-copying effecting call by reference."""
    def __init__(self, obj):
        self._obj = obj

    def unref(self):
        return self._obj

    def __deepcopy__(self, memo):
        return self

    def __serialize__(self, pack):
        return pack(self._obj)

    @classmethod
    def __construct__(cls, data):
        return Ref(data)


def ref(value):
    return Ref(value)


@schedule
def delay(value):
    """Creates a promise of a given value. TODO: this function should have a
    different name."""
    return value


@schedule
def gather(*a):
    """Converts a list of promises (i.e. :class:`PromisedObject`) to a promised
    list of values."""
    return list(a)


def gather_all(a):
    """Converts an iterator of promises into a promise of a list."""
    return gather(*a)


@schedule
def gather_dict(**kwargs):
    """Creates a promise of a dictionary."""
    return dict(**kwargs)


def unpack(t, n):
    """Iterates over a promised sequence, the sequence should support random
    access by :meth:`object.__getitem__`. Also the length of the sequence
    should be known beforehand.

    :param t: a sequence.
    :param n: the length of the sequence.
    :return: an unpackable generator for the elements in the sequence."""
    return (t[i] for i in range(n))


@schedule
def set_dict(obj, d):
    """Set the :attr:`object.__dict__` of `obj`.

    :param obj: input object.
    :param d: dictionary.
    :return: the modified object."""
    if d:
        obj.__dict__ = d
    return obj


@schedule
def create_object(cls, members):
    """Promise an object of class `cls` with content `members`."""
    obj = cls.__new__(cls)
    obj.__dict__ = members
    return obj


@schedule
def make_tuple(*args):
    """Promise a tuple."""
    return args


@schedule
def make_dict(*kwargs):
    """Promise a dictionary, from a list of 2-tuples."""
    return dict(kwargs)


@schedule
def make_list(*args):
    """Promise a list explicitely; function is identical to :func:`gather`."""
    return list(args)


@schedule
def make_set(*args):
    """Promise a set."""
    return set(args)


class Quote:
    """Quote objects store the contents of a workflow, allowing the workflow to
    be passed as an argument to a higher order function without its contents
    being evaluated. Don't use this object, rather use the functions
    :func:`quote` and :func:`unquote`."""
    def __init__(self, promise):
        self.workflow = promise._workflow

    @property
    def promise(self):
        return PromisedObject(self.workflow)


def quote(promise):
    """Quote a promise."""
    if isinstance(promise, PromisedObject):
        return Quote(promise)
    return promise


def unquote(quoted):
    """Unquote a quoted promise."""
    if isinstance(quoted, Quote):
        return quoted.promise
    return quoted


@schedule
def construct_object(cls, args):
    return cls(args)


@schedule
def simple_lift(obj):
    """Create a promise from a plain object."""
    return obj


def lift(obj, memo=None):
    """Make a promise out of object `obj`, where `obj` may contain promises
    internally.

    :param obj: Any object.
    :param memo: used for internal caching (similar to :func:`deepcopy`).

    If the object is a :class:`PromisedObject`, or *pass-by-value*
    (:class:`str`, :class:`int`, :class:`float`, :class:`complex`) it is
    returned as is.

    If the object's `id` has an entry in `memo`, the value from `memo` is
    returned.

    If the object has a method `__lift__`, it is used to get the promise.
    `__lift__` should take one additional argument for the `memo` dictionary,
    entirely analogous to :func:`deepcopy`.

    If the object is an instance of one of the basic container types (list,
    dictionary, tuple and set), we use the analogous function
    (:func:`make_list`, :func:`make_dict`, :func:`make_tuple`, and
    :func:`make_set`) to promise their counterparts should these objects
    contain any promises.  First, we map all items in the container through
    :func:`lift`, then check the result for any promises.  Note that in the
    case of dictionaries, we lift all the items (i.e. the list of key/value
    tuples) and then construct a new dictionary.

    If the object is an instance of a subclass of any of the basic container
    types, the `__dict__` of the object is lifted as well as the object cast
    to its base type. We then use :func:`set_dict` to set the `__dict__` of
    the new promise. Again, if the object did not contain any promises,
    we return it without change.

    Otherwise, we lift the `__dict__` and create a promise of a new object of
    the same class as the input, using :func:`create_object`. This works fine
    for what we call *reasonable* objects. Since calling :func:`lift` is an
    explicit action, we do not require reasonable objects to be derived from
    :class:`Reasonable` as we do with serialisation, where such a default
    behaviour could lead to unexplicable bugs."""
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
        dict:  (lambda x: list(x.items()), make_dict),
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
            internal = construct_object(obj.__class__, internal)
            rv = set_dict(internal, members)
        elif isinstance(members, PromisedObject):
            rv = set_dict(obj.__class__(internal), members)
        else:
            rv = obj

        memo[id(obj)] = rv
        return rv

    try:
        members = lift(obj.__dict__, memo)
        if isinstance(members, PromisedObject):
            rv = create_object(obj.__class__, members)
        else:
            rv = obj
    except AttributeError:
        memo[id(obj)] = obj
        return obj

    memo[id(obj)] = rv
    return rv
