"""
A base class for making objects serializable to JSON.
"""

from .utility import map_dict
from .decorator import PromisedObject, schedule
from copy import deepcopy


class StorableMeta(type):
    """
    The Storable metaclass registers all known classes that are derived from
    :py:class`Storable`, so that we know how to reconstruct them when we
    encounter one in a JSON file.
    """
    def __new__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            cls.registry = {}
        else:
            interface_id = name.lower()
            cls.registry[interface_id] = cls

        super(StorableMeta, cls).__init__(name, bases, dct)


@schedule
def storable_from_dict(cls, **kwargs):
    pass


class Storable(object):
    __metaclass__ = StorableMeta

    @classmethod
    def from_dict(cls, **kwargs):
        obj = cls.__new__(cls)
        obj.__dict__ = kwargs
        return obj

    def __deepcopy__(self, memo):
        cls = self.__class__
        if any(isinstance(x, PromisedObject) for x in self.__dict__.values()):
            return schedule(cls.from_dict)(**self.__dict__)
        else:
            return cls.from_dict(**map_dict(
                lambda x: deepcopy(x, memo), self.__dict__))
