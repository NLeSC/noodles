from functools import (wraps)
from itertools import (chain)
import inspect
from ..utility import (object_name)


class Fail:
    def __init__(self, func, fails=None, exception=None):
        self.name = "{} ({}:{})".format(
            object_name(func),
            inspect.getsourcefile(func),
            inspect.getsourcelines(func)[1])
        self.fails = fails or []
        self.trace = []
        self.exception = exception

    def add_call(self, func):
        self.trace.append("{} ({}:{})".format(
            object_name(func),
            inspect.getsourcefile(func),
            inspect.getsourcelines(func)[1]))

        return self

    @property
    def is_root_cause(self):
        return self.exception is not None

    def __bool__(self):
        return False

    def __str__(self):
        msg = "Fail: " + " -> ".join(self.trace + [self.name])
        if self.exception is not None:
            msg += "\n* exception: "
            msg += "\n    ".join(l for l in str(self.exception).split('\n'))
        elif self.fails:
            msg += "\n* failed arguments:\n    "
            msg += "\n    ".join(
                    "{} `{}` ".format(foo, bar) + "\n    ".join(
                        l for l in str(fail).split('\n'))
                    for foo, bar, fail in self.fails)
        return msg


def maybe(f):
    """Calls `f` in a try/except block, returning a `Fail` object if
    the call fails in any way. If any of the arguments to the call are Fail
    objects, the call is not attempted."""

    name = object_name(f)

    @wraps(f)
    def maybe_wrapped(*args, **kwargs):
        fails = [(name, k, v)
            for k, v in chain(enumerate(args), kwargs.items())
            if isinstance(v, Fail)]

        if fails:
            return Fail(f, fails=fails)

        try:
            result = f(*args, **kwargs)

        except Exception as e:
            return Fail(f, exception=e)

        else:
            if isinstance(result, Fail):
                result.add_call(f)

            return result

    return maybe_wrapped
