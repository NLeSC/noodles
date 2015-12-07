"""
A base class for making objects serializable to JSON.
"""

from .utility import map_dict
from .decorator import PromisedObject, schedule
from copy import deepcopy


def storable(obj):
    return isinstance(obj, Storable)


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


def copy_if_normal(memo):
    def f(obj):
        if isinstance(obj, PromisedObject):
            return obj
        else:
            return deepcopy(obj, memo)

    return f


def from_dict(cls, **kwargs):
    obj = cls.__new__(cls)
    obj.__dict__ = kwargs
    return obj


class Storable:
    @classmethod
    def from_dict(cls, **kwargs):
        obj = cls.__new__(cls)
        obj.__dict__ = kwargs
        return obj

    def __deepcopy__(self, memo):
        cls = self.__class__
        tmp = map_dict(copy_if_normal(memo), self.__dict__)

        if any(isinstance(x, PromisedObject) for x in tmp.values()):
            return schedule(from_dict)(cls, **tmp)
        else:
            return cls.from_dict(**tmp)
