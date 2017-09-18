from noodles import (schedule, quote, unquote)


def find_first(pred, lst):
    """Find the first result of a list of promises `lst` that satisfies a
    predicate `pred`.

    :param pred: a function of one argument returning `True` or `False`.
    :param lst: a list of promises or values.
    :return: a promise of a value or `None`.

    This is a wrapper around :func:`s_find_first`. The first item on the list
    is passed *as is*, forcing evalutation. The tail of the list is quoted, and
    only unquoted if the predicate fails on the result of the first promise.

    If the input list is empty, `None` is returned."""
    if lst:
        return s_find_first(pred, lst[0], [quote(l) for l in lst[1:]])
    else:
        return None


@schedule
def s_find_first(pred, first, lst):
    """Evaluate `first`; if predicate `pred` succeeds on the result of `first`,
    return the result; otherwise recur on the first element of `lst`.

    :param pred: a predicate.
    :param first: a promise.
    :param lst: a list of quoted promises.
    :return: the first element for which predicate is true."""
    if pred(first):
        return first
    elif lst:
        return s_find_first(pred, unquote(lst[0]), lst[1:])
    else:
        return None
