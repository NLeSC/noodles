from inspect import isfunction, ismethod
from itertools import count
from pathlib import Path
import base64

from ..interface import (PromisedObject, Quote)
from ..lib import (object_name, look_up, importable)
from ..workflow import (Workflow, NodeData, FunctionNode, ArgumentAddress,
                        ArgumentKind, reset_workflow, get_workflow)

from .registry import (Registry, Serialiser, SerUnknown)
from .reasonable import (Reasonable, SerReasonableObject)
from .path import (SerPath)


class SerAuto(Serialiser):
    def __init__(self):
        super(SerAuto, self).__init__('<automagic>')

    def encode(self, obj, make_rec):
        return obj.__serialize__(make_rec)

    def decode(self, cls, data):
        return cls.__construct__(data)


class SerDict(Serialiser):
    def __init__(self):
        super(SerDict, self).__init__(dict)

    def encode(self, obj, make_rec):
        return make_rec(dict(obj))

    def decode(self, cls, data):
        return cls(data)


class SerBytes(Serialiser):
    def __init__(self):
        super(SerBytes, self).__init__(bytes)

    def encode(self, obj, make_rec):
        return make_rec(base64.b64encode(obj).decode())

    def decode(self, cls, data):
        return base64.b64decode(data.encode())


class SerTuple(Serialiser):
    """Tuples get converted to lists during serialisation.
    We want to get tuples back, so make this explicit."""
    def __init__(self):
        super(SerTuple, self).__init__(tuple)

    def encode(self, obj, make_rec):
        return make_rec(list(obj))

    def decode(self, cls, data):
        return cls(data)


class SerEnum(Serialiser):
    def __init__(self, cls):
        super(SerEnum, self).__init__(cls)

    def encode(self, obj, make_rec):
        return make_rec(obj.name)

    def decode(self, cls, data):
        return cls[data]


class SerNamedTuple(Serialiser):
    def __init__(self, cls):
        super(SerNamedTuple, self).__init__(cls)

    def encode(self, obj, make_rec):
        return make_rec(dict(obj._asdict()))

    def decode(self, cls, data):
        return cls(**data)


class SerSlice(Serialiser):
    def __init__(self):
        super(SerSlice, self).__init__(slice)

    def encode(self, obj, make_rec):
        return make_rec([obj.start, obj.stop, obj.step])

    def decode(self, cls, data):
        return slice(*data)


def _remap_links(remap, links):
    return [{'node': remap[source],
             'to': [{'node': remap[node],
                     'address': address}
                    for node, address in target]}
            for source, target in links.items()]


class SerWorkflow(Serialiser):
    def __init__(self):
        super(SerWorkflow, self).__init__(Workflow)

    def encode(self, obj, make_rec):
        remap = dict(zip(obj.nodes.keys(), count()))
        return make_rec({'root': remap[obj.root],
                         'nodes': list(obj.nodes.values()),
                         'links': _remap_links(remap, obj.links)})

    def decode(self, cls, data):
        root = data['root']

        nodes = dict(zip(count(), data['nodes']))

        links = {l['node']: {(target['node'], target['address'])
                             for target in l['to']}
                 for l in data['links']}

        return reset_workflow(Workflow(root, nodes, links))


class SerPromisedObject(Serialiser):
    def __init__(self):
        super(SerPromisedObject, self).__init__(PromisedObject)

    def encode(self, obj, make_rec):
        return make_rec({'workflow': get_workflow(obj)})

    def decode(self, cls, data):
        return PromisedObject(data['workflow'])


class SerMethod(Serialiser):
    def __init__(self):
        super(SerMethod, self).__init__('<method>')

    def encode(self, obj, make_rec):
        return make_rec({'class': object_name(obj.__member_of__),
                         'method': obj.__name__})

    def decode(self, cls, data):
        cls = look_up(data['class'])
        return getattr(cls, data['method'])


class SerBoundMethod(Serialiser):
    def __init__(self):
        super(SerBoundMethod, self).__init__('<boundmethod>')

    def encode(self, obj, make_rec):
        return make_rec({
            'self': obj.__self__,
            'name': obj.__name__})

    def decode(self, _, data):
        return getattr(data['self'], data['name'])


class SerImportable(Serialiser):
    def __init__(self):
        super(SerImportable, self).__init__('<importable>')

    def encode(self, obj, make_rec):
        return make_rec(object_name(obj))

    def decode(self, cls, data):
        return look_up(data)


class SerNode(Serialiser):
    def __init__(self):
        super(SerNode, self).__init__(FunctionNode)

    def encode(self, obj, make_rec):
        return make_rec(dict(obj.data._asdict()))

    def decode(self, cls, data):
        return FunctionNode.from_node_data(NodeData(**data))


def _noodles_hook(obj):
    if '__member_of__' in dir(obj) and obj.__member_of__:
        return '<method>'

    if importable(obj):
        return '<importable>'

    if ismethod(obj):
        return '<boundmethod>'

    if isfunction(obj):
        return '<importable>'

    if hasattr(obj, '__serialize__') and hasattr(type(obj), '__construct__'):
        return '<automagic>'

    return None


def registry():
    """Returns the Noodles base serialisation registry."""
    return Registry(
        types={
            dict: SerDict(),
            tuple: SerTuple(),
            bytes: SerBytes(),
            slice: SerSlice(),
            Reasonable: SerReasonableObject(Reasonable),
            ArgumentKind: SerEnum(ArgumentKind),
            FunctionNode: SerNode(),
            ArgumentAddress: SerNamedTuple(ArgumentAddress),
            Workflow: SerWorkflow(),
            PromisedObject: SerPromisedObject(),
            Quote: SerReasonableObject(Quote),
            Path: SerPath()
        },
        hooks={
            '<method>': SerMethod(),
            '<boundmethod>': SerBoundMethod(),
            '<importable>': SerImportable(),
            '<automagic>': SerAuto()
        },
        hook_fn=_noodles_hook,
        default=SerUnknown(),
    )
