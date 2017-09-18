from typing import (Any, Callable, Iterable)
from noodles import (gather, unpack)


def fold(
        fun: Callable, acc: Any, xs: Iterable):
    """
    Traverse an iterable object while performing stateful computations
    with the elements. It returns a :py:class:`PromisedObject` containing
    the result of the stateful computations.

    For a general definition of folding see:
    https://en.wikipedia.org/wiki/Fold_(higher-order_function)

    A simple example::


    :param fun: stateful function.
    :param acc: initial state.
    :param xs: iterable object.
    :returns: :py:class:`PromisedObject`
    """
    def generator(acc):
        for x in xs:
            acc, r = unpack(fun(acc, x), 2)
            yield r

    return gather(*generator(acc))


def filter(pred: Callable, xs: Iterable):
    """
    Applied a predicate to a list returning a :py:class:`PromisedObject`
    containing the values satisfying the predicate.

    :param pred: predicate function.
    :param xs: iterable object.
    :returns: :py:class:`PromisedObject`
    """
    def generator():
        for x in xs:
            b = pred(x)
            if b:
                yield x

    return gather(*generator())
