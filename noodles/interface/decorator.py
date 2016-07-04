from functools import wraps
from copy import deepcopy
import hashlib
# import operator
import sys
import inspect

from ..workflow import (from_call, get_workflow)

from noodles.config import config


def scheduled_function(f, hints=None):
    """
    The Noodles schedule function decorator.

    The decorated function will return a workflow in stead of
    being applied immediately. This workflow can then be passed to a job
    scheduler in order to be run on any architecture supporting the current
    python environment.
    """
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

    return wrapped


def schedule(f):
    return scheduled_function(f)


def has_scheduled_methods(cls):
    for name, member in cls.__dict__.items():
        if hasattr(member, '__wrapped__'):
            member.__wrapped__.__member_of__ = cls

    return cls


def schedule_hint(**hints):
    return lambda f: scheduled_function(f, hints)


def unwrap(f):
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
    root = obj._workflow.root
    obj._workflow.nodes[root].hints.update(data)


def get_result(obj):
    root = obj._workflow.root
    return obj._workflow.nodes[root].result


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
