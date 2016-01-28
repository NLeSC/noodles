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


def map_dict(f, d):
    return dict((k, f(v)) for k, v in d.items())


def unzip_dict(d):
    a = {}
    b = {}

    for k, (v, w) in d.items():
        a[k] = v
        b[k] = w

    return a, b


def deep_map_2(f, root):
    result = f(root)

    if isinstance(result, dict):
        return {k: deep_map_2(f, v) for k, v in result.items()}

    if isinstance(result, list) or isinstance(result, tuple):
        return [deep_map_2(f, v) for v in result]

    return result


def deep_map(f, root):
    """Passes all objects in a hierarchy through a function.

    If the function `f` returns either a `list` or a `dict`,
    the values in the return value are recursively passed through
    `f`. This function can be used as an alternative to JSON encoding
    with an object hook. Currently it is very hard to trigger the JSON
    encoder hook on an object that is derived from `list` or `dict`.

    Internally this function works on a stack(like list), so no recursive
    call is being made.

    :param f:
        Function taking an object, returning another representation
        of that object.
    :type f: Callable

    :param root:
        The root object to start with.
    :type root: Any

    :returns: In quasi code: `f(root).map(deep_map(f, -))`
    :rtype: Any"""
    memo = {}

    # stage 1: map all objects
    q = [root]

    while len(q) != 0:
        obj = q.pop()

        if id(obj) not in memo:
            jbo = f(obj)

            if isinstance(jbo, dict):
                q.extend(jbo.values())

            elif isinstance(jbo, list) or isinstance(jbo, tuple):
                q.extend(jbo)

            else:
                continue

            memo[id(obj)] = jbo


    # stage 2: redirect links to mapped objects
    for w in memo.values():
        if isinstance(w, dict):
            for k, v in w.items():
                if id(v) in memo:
                    w[k] = memo[id(v)]

        elif isinstance(w, list) or isinstance(jbo, tuple):
            for k, v in enumerate(w):
                if id(v) in memo:
                    w[k] = memo[id(v)]

    return memo.get(id(root), root)
