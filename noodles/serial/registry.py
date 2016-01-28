from queue import Queue
from ..utility import object_name, look_up, deep_map_2
import noodles
import json


def _chain_fn(a, b):
    def f(obj):
        first = a(obj)
        if first:
            return first

        return b(obj)

    return f


class RefObject:
    def __init__(self, rec):
        self.rec = rec


class Registry(object):
    def __init__(self, parent=None, types=None, hooks=None, hook_fn=None,
                 default=None):
        self._sers = parent._sers.copy() if parent else {}

        if types:
            for k, v in types.items():
                self[k] = v

        if hooks:
            self._sers.update(hooks)

        self[object] = default if default \
            else parent.default if parent \
            else Serialiser(object)

        if hook_fn and parent and parent._hook:
            self._hook = _chain_fn(hook_fn, parent._hook)
        else:
            self._hook = hook_fn if hook_fn \
                else parent._hook if parent \
                else None

    def __add__(self, other):
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
        m_n = object_name(cls)
        self._sers[m_n] = value

    def encode(self, obj, host=None):
        if obj is None:
            return None

        if type(obj) in [dict, list, str, int, float, bool, tuple]:
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
        if not '_noodles' in rec:
            return rec

        if rec.get('ref', False) and not deref:
            return RefObject(rec)

        typename = rec['type']
        if typename[0] == '<' and typename[-1] == '>':
            return self._sers[typename].decode(None, rec['data'])

        cls = look_up(typename)
        return self[cls].decode(cls, rec['data'])

    def to_json(self, obj, host=None):
        return json.dumps(deep_map_2(lambda o: self.encode(o, host), obj))

    def from_json(self, data, deref=False):
        return json.loads(data, object_hook=lambda o: self.decode(o, deref))


class Serialiser(object):
    def __init__(self, base):
        self.base = base

    def encode(self, obj, make_rec):
        msg = "Cannot encode {}: encoder for type `{}` is not implemented." \
            .format(obj, type(obj).__name__)

        raise NotImplementedError(msg)

    def decode(self, cls, data):
        msg = "Decoder for type `{}` is not implemented." \
            .format(cls.__name__)

        raise NotImplementedError(msg)

