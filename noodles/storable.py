"""
A base class for making objects serializable to JSON.
"""

from .utility import map_dict
from .decorator import PromisedObject, schedule
from copy import deepcopy


def storable(obj):
    return isinstance(obj, Storable)


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
