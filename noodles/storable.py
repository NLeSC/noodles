"""
A base class for making objects serializable to JSON.
"""

from .utility import map_dict
from .decorator import PromisedObject, schedule
from .data_node import look_up
from copy import deepcopy

import uuid
import pickle
import base64


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


class StorableTraits:
    def __init__(self, ref, files):
        self.ref = ref
        self.files = files if files else []


class Storable:
    def __init__(self, ref=False, files=None):
        """Storable constructor

        :param ref:
            if this is True, the Storable is loaded as a
            :py:class:`StorableRef`, only to be restored when the data is
            really needed. This should be set to True for any object that
            carries a lot of data; the default is False.
        :type ref: bool

        :param files:
            the list of filenames that this object uses for
            storage. The property Storable.files is used by Noodles to copy
            relevant data if this object is needed on another host.
        :type files: [str]
        """
        self._noodles = StorableTraits(ref, files)

    @property
    def files(self):
        """List of files that this object saves to."""
        return self._noodles.files

    def as_dict(self):
        """Converts the object to a `dict` containing the members
        of the object by name.

        The default implementation is just
        ::

            def as_dict(self):
                return self.__dict__

        In most cases, this method is overloaded to provide a more
        advanced method of serializing data, possibly saving data to
        an external file. In this case the corresponding filename needs
        to be appended to `self.files`.
        """
        return self.__dict__

    @classmethod
    def from_dict(cls, **kwargs):
        """Gets a dictionary by `**kwargs`, and restores the original
        object. For any object `obj` of type `cls` that is derived from
        `Storable`, the following should  be true:
        ::

            cls.from_dict(**obj.as_dict()) == obj

        """
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


class StorableRef:
    """A reference to a storable object, containing
    only the JSON content needed to restore the original.

    When a Storable is recieved by the scheduler in  JSON form,
    the JSON is first stored in a StorableRef. Only when loaded by
    a worker it is converted back to the Storable.
    """

    def __init__(self, data):
        self.data = data

    def make(self):
        meta = self.data['_noodles']
        cls = look_up(meta['module'], meta['name'])
        return cls.from_dict(**self.data['data'])
