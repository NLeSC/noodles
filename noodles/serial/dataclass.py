from .registry import Serialiser


class SerDataClass(Serialiser):
    def __init__(self):
        super(SerDataClass, self).__init__('<dataclass>')

    def encode(self, obj, make_rec):
        return make_rec(obj.__dict__)

    def decode(self, cls, data):
        return cls(**data)
