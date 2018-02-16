"""
Maybe
=====

Facility to handle non-fatal errors in Noodles.
"""

from functools import (wraps)
from itertools import (chain)
import inspect
from ..lib import (object_name)


class Fail:
    """Signifies a failure in a computation that was wrapped by a ``@maybe``
    decorator. Because Noodles runs all functions from the same context, it
    is not possible to use Python stack traces to find out where an error
    happened. In stead we use a ``Fail`` object to store information about
    exceptions and the subsequent continuation of the failure."""
    def __init__(self, func, fails=None, exception=None):
        try:
            self.name = "{} ({}:{})".format(
                object_name(func),
                inspect.getsourcefile(func),
                inspect.getsourcelines(func)[1])
        except AttributeError:
            self.name = "<{} instance>".format(func.__class__.__name__)

        self.fails = fails or []
        self.trace = []
        self.exception = exception

    def add_call(self, func):
        """Add a call to the trace."""
        self.trace.append("{} ({}:{})".format(
            object_name(func),
            inspect.getsourcefile(func),
            inspect.getsourcelines(func)[1]))

        return self

    @property
    def is_root_cause(self):
        """If the field ``exception`` is set in this object, it means
        that we are looking at the root cause of the failure."""
        return self.exception is not None

    def __bool__(self):
        return False

    def __str__(self):
        msg = "Fail: " + " -> ".join(self.trace + [self.name])
        if self.exception is not None:
            msg += "\n* {}: ".format(type(self.exception).__name__)
            msg += "\n    ".join(l for l in str(self.exception).split('\n'))
        elif self.fails:
            msg += "\n* failed arguments:\n    "
            msg += "\n    ".join(
                "{} `{}` ".format(func, source) + "\n    ".join(
                    l for l in str(fail).split('\n'))
                for func, source, fail in self.fails)
        return msg


def failed(obj):
    """Returns True if ``obj`` is an instance of ``Fail``."""
    return isinstance(obj, Fail)


def maybe(func):
    """Calls `f` in a try/except block, returning a `Fail` object if
    the call fails in any way. If any of the arguments to the call are Fail
    objects, the call is not attempted."""

    name = object_name(func)

    @wraps(func)
    def maybe_wrapped(*args, **kwargs):
        """@maybe wrapped version of ``func``."""
        fails = [
            (name, k, v)
            for k, v in chain(enumerate(args), kwargs.items())
            if isinstance(v, Fail)]

        if fails:
            return Fail(func, fails=fails)

        try:
            result = func(*args, **kwargs)

        except Exception as exc:
            return Fail(func, exception=exc)

        else:
            if isinstance(result, Fail):
                result.add_call(func)

            return result

    return maybe_wrapped
