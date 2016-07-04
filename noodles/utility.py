from importlib import import_module
# import sys
# from copy import copy
# from functools import partial


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


class on:
    def __init__(self, env, obj):
        self.env = env
        self.obj = obj

    def __getattr__(self, name):
        return lambda *args: on(self.env, self.env[name](self.obj, *args))


def deep_map(f, root):
    result = f(root)

    if isinstance(result, dict):
        return {k: deep_map(f, v) for k, v in result.items()}

    if isinstance(result, list) or isinstance(result, tuple):
        return [deep_map(f, v) for v in result]

    return result


def inverse_deep_map(f, root):
    if isinstance(root, dict):
        r = {k: inverse_deep_map(f, v) for k, v in root.items()}
    elif isinstance(root, list):
        r = [inverse_deep_map(f, v) for v in root]
    else:
        r = root

    return f(r)
