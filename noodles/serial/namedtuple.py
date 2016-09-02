from .registry import (Serialiser)


class SerNamedTuple(Serialiser):
    def __init__(self, cls):
        super(SerNamedTuple, self).__init__(cls)

    def encode(self, obj, make_rec):
        return make_rec(tuple(obj))

    def decode(self, cls, data):
        return cls(*data)
