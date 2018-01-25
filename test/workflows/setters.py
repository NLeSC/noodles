import noodles
from noodles.tutorial import accumulate
from .workflow_factory import workflow_factory
import sys


class my_dict(dict):
    def values(self):
        return list(super(my_dict, self).values())


@noodles.schedule
def word_length(x):
    return len(x)


@workflow_factory(
        result={'apple': 5, 'orange': 6, 'kiwi': 4})
def set_item():
    word_lengths = noodles.delay({})

    for word in ['apple', 'orange', 'kiwi']:
        word_lengths[word] = word_length(word)

    return word_lengths


@workflow_factory(
        result=15)
def methods_on_promises():
    word_lengths = noodles.delay(my_dict())

    for word in ['apple', 'orange', 'kiwi']:
        word_lengths[word] = word_length(word)

    return accumulate(word_lengths.values())


class uncopyable_dict(dict):
    def __init__(self):
        super(uncopyable_dict, self).__init__()

        # trying to copy sys.stdout will raise an error
        self._uncopyable = sys.stdout


@workflow_factory(
        raises=TypeError)
def set_item_error():
    word_lengths = noodles.delay(uncopyable_dict)

    for word in ['apple', 'orange', 'kiwi']:
        word_lengths[word] = word_length(word)

    return word_lengths


@workflow_factory(
        raises=TypeError)
def set_attr_error():
    obj = noodles.delay(uncopyable_dict)
    obj.attr = 42
    return obj
