from importlib import import_module


def object_name(obj):
    """Get the qualified name of an object. This will obtain both the module
    name from `__module__` and object name from `__name__`, and concatenate
    those with a '.'. Examples:

    >>> from math import sin
    >>> object_name(sin)
    'math.sin'

    >>> def f(x):
    ...     return x*x
    ...
    >>> object_name(f)
    '__main__.f'

    To have a qualified name, an object must be defined as a class or function
    in a module (``__main__`` is also a module). A normal instantiated object
    does not have a qualified name, even if it is defined and importable from a
    module.  Calling |object_name| on such an object will raise
    :py:exc:`AttributeError`.

    .. |object_name| replace:: :py:func:`object_name`"""
    return obj.__module__ + '.' + obj.__qualname__


def look_up(name):
    """Obtain an object from a qualified name. Example:

    >>> look_up('math.sin')
    <built-in function sin>

    This function should be considered the reverse of |object_name|.

    .. |look_up| replace:: :py:func:`look_up`"""
    path = name.split('.')
    module = import_module('.'.join(path[:-1]))
    return getattr(module, path[-1])


def importable(obj):
    """Check if an object can be serialised as a qualified name. This is done
    by checking that a ``look_up(object_name(obj))`` gives back the same
    object.

    .. |importable| replace:: :py:func:`importable`"""
    try:
        return look_up(object_name(obj)) is obj
    except (AttributeError, TypeError, ImportError):
        return False


def unzip_dict(d):
    a = {}
    b = {}

    for k, (v, w) in d.items():
        a[k] = v
        b[k] = w

    return a, b


def unwrap(f):
    """Safely obtain the inner function of a previously wrapped (or decorated)
    function. This either returns ``f.__wrapped__`` or just ``f`` if the latter
    fails.

    .. |unwrap| replace:: :py:func:`unwrap`"""
    try:
        return f.__wrapped__
    except AttributeError:
        return f


def is_unwrapped(f):
    """If `f` was imported and then unwrapped, this function might return True.

    .. |is_unwrapped| replace:: :py:func:`is_unwrapped`"""
    try:
        g = look_up(object_name(f))
        return g != f and unwrap(g) == f

    except (AttributeError, TypeError, ImportError):
        return False


def deep_map(f, root):
    """Sibling to |inverse_deep_map|. As :py:func:`map` maps over an iterable,
    |deep_map| maps over a structure of nested ``dict``s and ``list``s. Every
    object is passed through `f` recursively. That is, first `root` is mapped,
    next any object contained in its result, and so on.

    No distinction is made between tuples and lists. This function was
    created with encoding to JSON compatible data in mind.

    .. |deep_map| replace:: :py:func:`deep_map`"""
    result = f(root)

    if isinstance(result, dict):
        return {k: deep_map(f, v) for k, v in result.items()}

    if isinstance(result, list) or isinstance(result, tuple):
        return [deep_map(f, v) for v in result]

    return result


def inverse_deep_map(f, root):
    """Sibling to |deep_map|. Recursively maps objects in a nested structure of
    ``list`` and ``dict`` objects. Where |deep_map| starts at the top,
    |inverse_deep_map| starts at the bottom. First, if `root` is a ``list`` or
    ``dict``, its contents are |inverse_deep_map|ed. Then at the end, the
    entire object is passed through `f`.

    This function was created with decoding from JSON compatible data in mind.

    .. |inverse_deep_map| replace:: :py:func:`inverse_deep_map`"""
    if isinstance(root, dict):
        r = {k: inverse_deep_map(f, v) for k, v in root.items()}
    elif isinstance(root, list):
        r = [inverse_deep_map(f, v) for v in root]
    else:
        r = root

    return f(r)
