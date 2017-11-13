from .registry import Serialiser


class Reasonable(object):
    """A Reasonable object is an object which is most reasonably serialised
    using its `__dict__` property. To deserialise the object, we first create
    an instance using the `__new__` method, then setting the `__dict__`
    property manualy. This class is empty, it is used as a tag to designate
    other objects as reasonable."""
    pass
    

class SerReasonableObject(Serialiser):
    def __init__(self, cls):
        super(SerReasonableObject, self).__init__(cls)
        
    def encode(self, obj, make_rec):
        return make_rec(obj.__dict__)
        
    def decode(self, cls, data):
        obj = cls.__new__(cls)
        obj.__dict__ = data
        return obj

