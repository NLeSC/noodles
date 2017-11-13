"""
.. default-domain:: py
"""

from functools import wraps
from copy import deepcopy
import hashlib
# import operator
import sys
import inspect

from ..workflow import (from_call, get_workflow)

from noodles.config import config


def scheduled_function(f, hints=None):
    """The Noodles schedule function decorator.

    The decorated function will return a workflow in stead of
    being applied immediately. This workflow can then be passed to a job
    scheduler in order to be run on any architecture supporting the current
    python environment."""
    if hints is None:
        hints = {}

    if 'version' not in hints:
        try:
            source_bytes = inspect.getsource(f).encode()
            m = hashlib.md5()
            m.update(source_bytes)
            hints['version'] = m.hexdigest()

        except:
            pass

    @wraps(f)
    def wrapped(*args, **kwargs):
        return PromisedObject(from_call(
            f, args, kwargs, deepcopy(hints),
            call_by_value=config['call_by_value']))

    # add *(scheduled)* to the beginning of the docstring.
    if hasattr(wrapped, '__doc__') and wrapped.__doc__ is not None:
        wrapped.__doc__ = "*(scheduled)* " + wrapped.__doc__

    return wrapped


def schedule(f):
    """Decorator; schedule calls to function `f` into a workflow, in stead of
    running them at once. The decorated function returns a
    :class:`PromisedObject`."""
    return scheduled_function(f)


def has_scheduled_methods(cls):
    """Decorator; use this on a class for which some methods have been
    decorated with :func:`schedule` or :func:`schedule_hint`. Those methods
    are then tagged with the attribute `__member_of__`, so that we may
    serialise and retrieve the correct method. This should be considered
    a patch to a flaw in the Python object model."""
    for member in cls.__dict__.values():
        if hasattr(member, '__wrapped__'):
            member.__wrapped__.__member_of__ = cls

    return cls


def schedule_hint(**hints):
    """Decorator; same as :func:`schedule`, with added hints. These
    hints can be anything."""
    return lambda f: scheduled_function(f, hints)


def unwrap(f):
    """Unwrap a wrapped function; the function needs to have been wrapped
    using :func:`functools.wraps`, as is done in :func:`schedule`.

    If function `f` doesn't have the `__wrapped` attribute, the same
    function `f` is returned."""
    try:
        return f.__wrapped__
    except AttributeError:
        return f


@schedule
def _getitem(obj, ix):
    return obj[ix]


@schedule
def _getattr(obj, attr):
    return getattr(obj, attr)


@schedule
def _setattr(obj, attr, value):
    try:
        obj = deepcopy(obj)
        obj.__setattr__(attr, value)

    except TypeError as err:
        tb = sys.exc_info()[2]
        from pprint import PrettyPrinter
        pp = PrettyPrinter()
        obj_repr = "<" + obj.__class__.__name__ + ">: " \
            + pp.pformat(obj.__dict__)
        msg = "In `_setattr` we deepcopy the object *during runtime*. " \
              "If you're sure that what you're doing is safe, you can " \
              " overload `__deepcopy__` to get more efficient code. " \
              "However, something went " \
              "wrong here: \n" + err.args[0] + '\n' + obj_repr
        raise TypeError(msg).with_traceback(tb)

    return obj


@schedule
def _do_call(obj, *args, **kwargs):
    return obj(*args, **kwargs)


def update_hints(obj, data):
    """Update the hints on the root-node of a workflow. Usually, schedule
    hints are fixed per function. Sometimes a user may want to set hints
    manually on a specific promised object. :func:`update_hints` uses the
    `update` method on the hints dictionary with `data` as its argument.

    :param obj: a :class:`PromisedObject`.
    :param data: a :class:`dict` containing additional hints.

    The hints are modified, in place, on the node. All workflows that contain
    the node are affected."""
    root = obj._workflow.root
    obj._workflow.nodes[root].hints.update(data)


def result(obj):
    """Results are stored on the nodes in the workflow at run time. This
    function can be used to get at a result of a node in a workflow after
    run time. This is not a recommended way of getting at results, but can
    help with debugging."""
    return obj.__result__()


class ConstRef:
    def __init__(self, this):
        self.this = this

    def __getattr__(self, attr):
        return getattr(self.this, attr)

    def __deepcopy__(self, _):
        return self


class PromisedObject:
    """
    Wraps a :py:class:`Workflow`. The workflow represents the future promise
    of a Python object. By wrapping the workflow, we can mock the behaviour of
    this future object and schedule methods that were called by the user
    as if nothing weird is going on.
    """
    def __init__(self, workflow):
        self._workflow = workflow

    def __call__(self, *args, **kwargs):
        return _do_call(self._workflow, *args, **kwargs)

    def __getattr__(self, attr):
        return _getattr(self, attr)

    def __setattr__(self, attr, value):
        if attr[0] == '_':
            self.__dict__[attr] = value
            return

        self._workflow = get_workflow(
            _setattr(self, attr, value))

    def __result__(self):
        return self._workflow.root_node.result

    # predicates
    # def __lt__(self, other):
    #     return schedule(operator.lt)(self, other)

    # def __gt__(self, other):
    #     return schedule(operator.gt)(self, other)

    # def __eq__(self, other):
    #     return schedule(operator.eq)(self, other)

    # def __ne__(self, other):
    #     return schedule(operator.ne)(self, other)

    # def __ge__(self, other):
    #     return schedule(operator.ge)(self, other)

    # def __le__(self, other):
    #     return schedule(operator.le)(self, other)

    #  boolean operations
    # def __bool__(self):
    #     return schedule(operator.truth)(self)

    # numerical operations
    # def __abs__(self):
    #     return schedule(operator.abs)(self)

    # def __sub__(self, other):
    #     return schedule(operator.sub)(self, other)

    # def __add__(self, other):
    #     return schedule(operator.add)(self, other)

    # def __mul__(self, other):
    #     return schedule(operator.mul)(self, other)

    # def __truediv__(self, other):
    #     return schedule(operator.truediv)(self, other)

    # def __floordiv__(self, other):
    #     return schedule(operator.floordiv)(self, other)

    # def __mod__(self, other):
    #     return schedule(operator.mod)(self, other)

    # def __pow__(self, other):
    #     return schedule(operator.pow)(self, other)

    # def __pos__(self):
    #     return schedule(operator.pos)(self)

    # def __neg__(self):
    #     return schedule(operator.neg)(self)

    # def __matmul__(self, other):
    #     return schedule(operator.matmul)(self, other)

    # def __index__(self):
    #     return schedule(operator.index)(self)

    # bit operations
    # def __inv__(self):
    #     return schedule(operator.inv)(self)

    # def __lshift__(self, n):
    #     return schedule(operator.lshift)(self, n)

    # def __rshift__(self, n):
    #     return schedule(operator.rshift)(self, n)

    # def __and__(self, other):
    #     return schedule(operator.and_)(self, other)

    # def __or__(self, other):
    #     return schedule(operator.or_)(self, other)

    # def __xor__(self, other):
    #     return schedule(operator.xor)(self, other)

    # container operations
    # def __contains__(self, item):
    #    return schedule(operator.contains)(self, item)

    def __getitem__(self, name):
        return _getitem(self, name)

    # undefined behaviour
    def __iter__(self):
        raise TypeError(
            "You have tried to iterate (or unpack) a PromisedObject. "
            "There is currently no possible way to learn the "
            "length of a PromisedObject so, sadly, this is not "
            "implemented. You may use the `noodles.unpack` function "
            "to unpack a promised tuple.")

    def __deepcopy__(self, _):
        # rnode = self._workflow.nodes[self._workflow.root]
        # from pprint import PrettyPrinter
        raise TypeError(
            "A PromisedObject cannot be deepcopied. Most probably, you "
            "have a promise stored in another object, which you passed to "
            "a scheduled function. To transform an object with nested "
            "promises to a top-level promise, apply the `lift` function.")
