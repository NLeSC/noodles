from typing import (Iterable, Callable, TypeVar, Optional)

from noodles import (schedule, quote, unquote)

T = TypeVar('T')
Predicate = Callable[[T], bool]


def find_first(pred: Predicate[T], lst: Iterable[T]) -> Optional[T]:
    """Find the first result of an iterable of promises `lst` that satisfies a
    predicate `pred`.

    :param pred: a function of one argument returning `True` or `False`.
    :param lst: an iterable of promises or values.
    :return: a promise of a value or `None`.

    This is a wrapper around :func:`s_find_first`. The first item in the iterable
    is passed *as is*, forcing evalutation. The tail of the iterable is quoted, and
    only unquoted if the predicate fails on the result of the first promise.

    If the input iterable is empty, `None` is returned."""
    try:
        head, *tail = lst
    except ValueError:  # i.e. lst is too short
        return None
    else:
        return s_find_first(pred, head, [quote(l) for l in tail])


@schedule
def s_find_first(pred: Predicate[T], first: T, lst: Iterable[T]) -> Optional[T]:
    """Evaluate `first`; if predicate `pred` succeeds on the result of `first`,
    return the result; otherwise recur on the first element of `lst`.

    :param pred: a predicate.
    :param first: a promise.
    :param lst: an iterable of quoted promises.
    :return: the first element for which predicate is true."""
    if pred(first):
        return first

    try:
        head, *tail = lst
    except ValueError:  # i.e. lst is too short
        return None
    else:
        return s_find_first(pred, unquote(head), tail)
