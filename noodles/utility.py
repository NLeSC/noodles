from importlib import import_module
import sys
from copy import copy


def object_name(obj):
    return obj.__module__ + '.' + obj.__name__


def look_up(name):
    path = name.split('.')
    module = import_module('.'.join(path[:-1]))
    return getattr(module, path[-1])


def importable(obj):
    try:
        return look_up(object_name(obj)) is obj
    except:
        return False


def unzip_dict(d):
    a = {}
    b = {}

    for k, (v, w) in d.items():
        a[k] = v
        b[k] = w

    return a, b


def unwrap(f):
    try:
        return f.__wrapped__
    except AttributeError:
        return f


def deep_map(f, root):
    result = f(root)

    if isinstance(result, dict):
        return {k: deep_map(f, v) for k, v in result.items()}

    if isinstance(result, list) or isinstance(result, tuple):
        return [deep_map(f, v) for v in result]

    return result

