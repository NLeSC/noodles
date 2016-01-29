from .registry import (Serialiser, Registry)
from ..utility import look_up
import numpy
import uuid


class SerNumpyArray(Serialiser):
    def __init__(self, file_prefix=None):
        super(SerNumpyArray, self).__init__(numpy.ndarray)
        self.file_prefix = file_prefix if file_prefix else ''

    def encode(self, obj, make_rec):
        filename = self.file_prefix + str(uuid.uuid4()) + '.npy'
        numpy.save(filename, obj)
        return make_rec(filename, ref=True, files=[filename])

    def decode(self, cls, filename):
        return numpy.load(filename)


class SerUFunc(Serialiser):
    def __init__(self):
        super(SerUFunc, self).__init__(None)

    def encode(self, obj, make_rec):
        return make_rec('numpy.' + obj.name)

    def decode(self, cls, data):
        return look_up(data)


def _numpy_hook(obj):
    if isinstance(obj, numpy.ufunc):
        return '<ufunc>'

    return None


def registry(file_prefix=None):
    """Returns a serialisation registry for serialising NumPy data and
    as well as any UFuncs that have no normal way of retrieving
    qualified names."""
    return Registry(
        types={
            numpy.ndarray: SerNumpyArray(file_prefix)
        },
        hooks={
            '<ufunc>': SerUFunc()
        },
        hook_fn=_numpy_hook
    )
