from queue import Queue
from ..utility import (
    object_name, look_up, deep_map, inverse_deep_map)

import noodles

# try:
#    import ujson as json
# except ImportError:
import json

try:
    import msgpack
    has_msgpack = True
except ImportError:
    has_msgpack = False


def _chain_fn(a, b):
    def f(obj):
        first = a(obj)
        if first:
            return first

        return b(obj)

    return f


class RefObject:
    """Placeholder object to delay decoding a serialised object
    until needed by a worker."""
    def __init__(self, rec):
        self.rec = rec


class Registry(object):
    """Serialisation registry, keeps a record of `Serialiser` objects.

    The Registry keeps a dictionary mapping (qualified) class names to
    :py:class:`Serialiser` objects. Given an object, the `__getitem__`
    method looks for the highest base class that it has a serialiser for.
    As a fall-back we install a Serialiser matching the Python
    `object` class.

    Detection by object type is not always meaningful or even possible.
    Before scannning for known base classes the look-up function passes
    the object through the `hook` function, which should return a string
    or `None`. If a string is returned that string is used to look-up
    the serialiser.

    Registries can be combined using the '+' operator. The left side argument
    is than used as `parent` to the new Registry, while the right-hand argument
    overrides and augments the Serialisers present. The `hook` functions
    are being chained, such that the right-hand registry takes precedence.
    The default serialiser is inherrited from the left-hand argument.
    """
    def __init__(self, parent=None, types=None, hooks=None, hook_fn=None,
                 default=None):
        """Constructor

        :param parent:
            The new Registry takes the dictionary and hook from the parent.
            If no other argumentns are given, we get a copy of `parent`.
        :type parent: `Registry`

        :param types:
            A dictionary of types to Serialiser objects. Each of these
            are added to the new Registry.

        :param hooks:
            A dictionary of strings to Serialiser objects. These are added
            directly to the dictionary internal to the new Registry.

        :param hook_fn:
            A function taking an object returning a string. The string should
            match a string in the hook dictionary. It should not be possible
            to confuse the returned string with a qualified Python name.
            One way to do this, is by enclosing the string with
            '<' '>' characters.

        :param default:
            The default fall-back for the new Registry.
        :type default: `Serialiser`"""
        self._sers = parent._sers.copy() if parent else {}

        if types:
            for k, v in types.items():
                self[k] = v

        if hooks:
            self._sers.update(hooks)

        self.default = default if default \
            else parent.default if parent \
            else Serialiser(object)

        if hook_fn and parent and parent._hook:
            self._hook = _chain_fn(hook_fn, parent._hook)
        else:
            self._hook = hook_fn if hook_fn \
                else parent._hook if parent \
                else None

    def __add__(self, other):
        """Merge two registries. Right-side takes presedence over left-side
        argument, with exception of the default (fall-back) serialiser."""
        reg = Registry(
            parent=self, hooks=other._sers,
            hook_fn=other._hook, default=self.default)

        return reg

    @property
    def default(self):
        return self[object]

    @default.setter
    def default(self, ser):
        self[object] = ser

    def __getitem__(self, key):
        """Searches the most fitting serialiser based on the inheritance tree
        of the given class. We search this tree breadth-first."""
        q = Queue()  # use a queue for breadth-first decent

        q.put(key)
        while not q.empty():
            cls = q.get()
            m_n = object_name(cls)

            if m_n in self._sers:
                return self._sers[m_n]
            else:
                for base in cls.__bases__:
                    q.put(base)

    def __setitem__(self, cls, value):
        """Sets a new Serialiser for the given class."""
        m_n = object_name(cls)
        self._sers[m_n] = value

    def encode(self, obj, host=None):
        """Encode an object using the serialisers available
        in this registry. Objects that have a type that is one of
        [dict, list, str, int, float, bool, tuple] are send back unchanged.

        A host-name can be given as an additional argument to identify the
        host in the resulting record if the encoder yields any filenames.

        This function only treats the object for one layer deep.

        :param obj:
            The object that needs encoding.

        :param host:
            The name of the encoding host.
        :type host: str
        """
        if obj is None:
            return None

        if type(obj) in [dict, list, str, int, float, bool]:
            return obj

        if isinstance(obj, RefObject):
            return obj.rec

        hook = self._hook(obj) if self._hook else None
        typename = hook if hook else object_name(type(obj))

        def make_rec(data, ref=None, files=None):
            rec = {'_noodles': noodles.__version__,
                   'type': typename,
                   'data': data}

            if ref is not None:
                rec['ref'] = ref,

            if files:
                rec['host'] = host
                rec['files'] = files

            return rec

        if hook:
            return self._sers[hook].encode(obj, make_rec)

        enc = self[type(obj)]
        result = enc.encode(obj, make_rec)
        return result

    def decode(self, rec, deref=False):
        """Decode a record to return an object that could be considered
        equivalent to the original.

        The record is not touched if `_noodles` is not an item in the record.

        :param rec:
            A dictionary record to be decoded.
        :type rec: dict

        :param deref:
            Wether to decode a RefObject. If the encoder wrote files on a
            remote host, reading this file will be slow and result in an
            error if the file is not present.
        :type deref: bool"""
        if not isinstance(rec, dict):
            return rec

        if '_noodles' not in rec:
            return rec

        # if not deref:
        if rec.get('ref', False) and not deref:
            return RefObject(rec)

        typename = rec['type']
        if typename[0] == '<' and typename[-1] == '>':
            return self._sers[typename].decode(None, rec['data'])

        cls = look_up(typename)
        return self[cls].decode(cls, rec['data'])

    def deep_encode(self, obj, host=None):
        return deep_map(lambda o: self.encode(o, host), obj)

    def deep_decode(self, rec, deref=False):
        return inverse_deep_map(lambda r: self.decode(r, deref), rec)

    def to_json(self, obj, host=None, indent=None):
        """Recursively encode `obj` and convert it to a JSON string.

        :param obj:
            Object to encode.

        :param host:
            hostname where this object is being encoded.
        :type host: str"""
        if indent:
            return json.dumps(deep_map(lambda o: self.encode(o, host), obj),
                              indent=indent)
        else:
            return json.dumps(deep_map(lambda o: self.encode(o, host), obj))

    def to_msgpack(self, obj, host=None):
        return msgpack.packb(deep_map(lambda o: self.encode(o, host), obj))

    def from_json(self, data, deref=False):
        """Decode the string from JSON to return the original object (if
        `deref` is true. Uses the `json.loads` function with `self.decode`
        as object_hook.

        :param data:
            JSON encoded string.
        :type data: str

        :param deref:
            Whether to decode records that gave `ref=True` at encoding.
        :type deref: bool"""
        # return self.deep_decode(json.loads(data), deref)
        return json.loads(data, object_hook=lambda o: self.decode(o, deref))

    def from_msgpack(self, data, deref=False):
        return msgpack.unpackb(
            data,
            object_hook=lambda o: self.decode(o, deref))

    def dereference(self, data, host):
        """Dereferences RefObjects stuck in the hierarchy. This is a bit
        of an ugly hack."""
        return self.from_json(self.to_json(data, host), deref=True)


class Serialiser(object):
    """Serialiser base class.

    Serialisation classes should derive from `Serialiser` and overload the
    `encode` and `decode` methods.

    :param base:
        The type that this class is supposed to serialise. This may differ
        from the type of the object actually being serialised if its class
        was derived from `base`. The supposed base-class is kept here for
        reference but serves no immediate purpose.
    :type base: type"""
    def __init__(self, name):
        if isinstance(name, str):
            self.name = name
        else:
            try:
                self.name = name.__name__
            except AttributeError:
                self.name = '<unknown>'

    def encode(self, obj, make_rec):
        """Should encode an object of type `self.base` (or derived).

        This method receives the object and a function `make_rec`. This
        function has signature:

        .. code-block:: python

            def make_rec(rec, ref=False, files=None):
                ...

        If encoding and decoding is somewhat cosuming on resources, the
        encoder may call with `ref=True`. Then the resulting record won't
        be decoded until needed by the next job. This is most certainly
        the case when an external file was written. In this case the
        filename(s) should be passed as a list by `files=[...]`.

        The `files` list is not passed back to the decoder. Rather it is used
        by noodles to keep track of written files and copy them between hosts
        if needed. It is the responsibily of the encoder to include
        the filename information in the passed record as well.

        :param obj:
            Object to be encoded.

        :param make_rec:
            Function used to pack the encoded data with some meta-data."""
        if obj is None:
            raise RuntimeError("Object None should not reach encoder.")

        if hasattr(obj, '__serialize__'):
            return obj.__serialize__(make_rec)

        msg = "Cannot encode {}: encoder for type `{}` is not implemented." \
            .format(obj, type(obj).__name__)

        raise NotImplementedError(msg)

    @staticmethod
    def decode(cls, data):
        """Should decode the data to an object of type 'cls'.

        :param cls:
            The class is retrieved by the qualified name of the type
            of the object that was encoded; restored by importing it.
        :type cls: type

        :param data:
            The data is the record that was passed to `make_rec` by
            the encoder."""

        if hasattr(cls, '__construct__'):
            return cls.__construct__(data)

        msg = "Decoder for type `{}` is not implemented." \
            .format(cls.__name__)

        raise NotImplementedError(msg)
