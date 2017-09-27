from .find_first import find_first
from noodles import (gather, schedule, unpack)
from typing import (Any, Callable, Iterable)


@schedule
def all(pred: Callable, xs: Iterable):
    """
    Check whether all the elements of the iterable `xs`
    fullfill predicate `pred`.

    :param pred:
       predicate function
    :param xs:
       iterable object.
    :returns: boolean
    """
    for x in xs:
        if not pred(x):
            return False

    return True


@schedule
def any(pred: Callable, xs: Iterable):
    """
    Check if at least one element of the iterable `xs`
    fullfills predicate `pred`.

    :param pred:
       predicate function.
    :param xs:
       iterable object.
    :returns: boolean
    """
    b = find_first(pred, xs)

    return True if b is not None else False


@schedule
def filter(pred: Callable, xs: Iterable):
    """
    Applied a predicate to a list returning a :py:class:`PromisedObject`
    containing the values satisfying the predicate.

    :param pred: predicate function.
    :param xs: iterable object.
    :returns: :py:class:`PromisedObject`
    """
    generator = (x for x in xs if pred(x))

    return gather(*generator)


@schedule
def fold(
        fun: Callable, state: Any, xs: Iterable):
    """
    Traverse an iterable object while performing stateful computations
    with the elements. It returns a :py:class:`PromisedObject` containing
    the result of the stateful computations.

    For a general definition of folding see:
    https://en.wikipedia.org/wiki/Fold_(higher-order_function)

    :param fun: stateful function.
    :param state: initial state.
    :param xs: iterable object.
    :returns: :py:class:`PromisedObject`
    """
    def generator(state):
        for x in xs:
            state, r = unpack(fun(state, x), 2)
            yield r

    return gather(*generator(state))


@schedule
def map(fun: Callable, xs: Iterable):
    """
    Traverse an iterable object applying function `fun`
    to each element and finally creats a workflow from it.

    :param fun:
      function to call in each element of the iterable
      object.
    :param xs:
      Iterable object.

    returns::py:class:`PromisedObject`
    """
    generator = (fun(x) for x in xs)

    return gather(*generator)


@schedule
def zip_with(fun: Callable, xs: Iterable, ys: Iterable):
    """
    Fuse two Iterable object using the function `fun`.
    Notice that if the two objects have different len,
    the shortest object gives the result's shape.

    :param fun:
       function taking two argument use to process
       element x from `xs` and y from `ys`.

    :param xs:
       first iterable.

    :param ys:
       second iterable.

    returns::py:class:`PromisedObject`
    """
    generator = (fun(*rs) for rs in zip(xs, ys))

    return gather(*generator)
