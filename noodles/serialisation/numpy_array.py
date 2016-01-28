from .registry import (Serialiser, Registry)
from ..utility import look_up
import numpy
import uuid


class SerNumpyArray(Serialiser):
    def __init__(self):
        super(SerNumpyArray, self).__init__(numpy.ndarray)

    def encode(self, obj, make_rec):
        filename = uuid.uuid4() + '.npy'
        numpy.save(filename, obj)
        return make_rec(filename, ref=True, files=[filename])

    def decode(self, cls, filename):
        return numpy.load(filename)


class SerUFunc(Serialiser):
    def __init__(self):
        super(SerUFunc, self).__init__(None)

    def encode(self, obj, make_rec):
        return 'numpy.' + obj.name

    def decode(self, cls, data):
        return look_up(data)


def _numpy_hook(obj):
    if isinstance(obj, numpy.ufunc):
        return '<ufunc>'

    return None


numpy_registry = Registry(
    types={
        numpy.ndarray: SerNumpyArray()
    },
    hooks={
        '<ufunc>': SerUFunc()
    },
    hook_fn=_numpy_hook
)
