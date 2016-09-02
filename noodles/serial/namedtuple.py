from .registry import (Registry, Serialiser)
from ..utility import (object_name, look_up)


class SerNamedTuple(Serialiser):
    def __init__(self, cls):
        super(SerNamedTuple, self).__init__(cls)

    def encode(self, obj, make_rec):
        return make_rec(tuple(obj))

    def decode(self, cls, data):
        return cls(*data)


class SerAutoNamedTuple(Serialiser):
    def __init__(self):
        super(SerAutoNamedTuple, self).__init__('<namedtuple>')

    def encode(self, obj, make_rec):
        return make_rec({
            'name': object_name(type(obj)),
            'data': tuple(obj)})

    def decode(self, cls, data):
        return look_up(data['name'])(*data['data'])


def is_namedtuple(obj):
    return isinstance(obj, tuple) and hasattr(obj, '_fields')


def namedtuple_hook(obj):
    if is_namedtuple(obj):
        return '<namedtuple>'
    else:
        return None


def registry():
    return Registry(
        hooks={
            '<namedtuple>': SerAutoNamedTuple()
        },
        hook_fn=namedtuple_hook)
