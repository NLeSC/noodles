from . import (
    gather, conditionals, class_methods, unpack, lift, dict_likes,
    patterns)
from .workflow_factory import workflow_factory
from itertools import chain
from noodles.lib import unwrap


modules = [
    gather, conditionals, class_methods, unpack, lift, dict_likes,
]

workflows = dict(chain.from_iterable(
    ((item, getattr(module, item)) for item in dir(module)
     if isinstance(getattr(module, item), unwrap(workflow_factory)))
    for module in modules))

__all__ = ['workflows']
