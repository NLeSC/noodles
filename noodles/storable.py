"""
A base class for making objects serializable to JSON.
"""

from .utility import map_dict
from .decorator import PromisedObject, schedule
from .data_node import look_up
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
    obj = cls.from_dict(**kwargs)
    return obj


class Storable:
    def __init__(self, use_ref=False):
        self._use_ref = use_ref

    def as_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, **kwargs):
        obj = cls.__new__(cls)
        obj.__dict__ = kwargs
        return obj

    def __deepcopy__(self, memo):
        cls = self.__class__
        tmp = map_dict(copy_if_normal(memo), self.as_dict())

        if any(isinstance(x, PromisedObject) for x in tmp.values()):
            return schedule(from_dict)(cls, **tmp)
        else:
            return cls.from_dict(**tmp)


class StorableRef(dict):
    """A reference to a storable object, containing
    only the JSON content needed to restore the original.

    When a Storable is recieved by the scheduler in  JSON form,
    the JSON is first stored in a StorableRef. Only when loaded by
    a worker it is converted back to the Storable.
    """

    def __init__(self, data):
        super(StorableRef, self).__init__(data)

    def make(self):
        meta = self['_noodles']
        cls = look_up(meta['module'], meta['name'])
        return cls.from_dict(**self['data'])
