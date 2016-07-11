from ..serial import (Serialiser)


class Path:
    def __init__(self, path):
        self.path = path


class SerPath(Serialiser):
    def __init__(self):
        super(SerPath, self).__init__(Path)

    def encode(self, obj, make_rec):
        return make_rec({'path': obj.path}, files=[obj.path])

    def decode(self, cls, data):
        return cls(path=data['path'])
