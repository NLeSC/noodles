from .registry import (Serialiser)


class AsDict(Serialiser):
    def __init__(self, cls):
        super(AsDict, self).__init__(cls)

    def encode(self, obj, make_rec):
        return make_rec(obj.__dict__)

    def decode(self, cls, data):
        obj = cls.__new__(cls)
        obj.__dict__ = data
        return obj
