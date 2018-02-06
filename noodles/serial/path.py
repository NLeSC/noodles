from pathlib import Path
from .registry import (Serialiser)


class SerPath(Serialiser):
    def __init__(self):
        super(SerPath, self).__init__(Path)

    def encode(self, obj, make_rec):
        return make_rec(str(obj), files=[str(obj)])

    def decode(self, cls, data):
        return Path(data)
