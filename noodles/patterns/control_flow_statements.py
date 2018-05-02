from noodles import (schedule, quote, unquote)
from typing import Any


def conditional(
        b: bool,
        branch_true: Any,
        branch_false: Any=None) -> Any:
    """
    Control statement to follow a branch
    in workflow. Equivalent to the `if` statement
    in standard Python.

    The quote function delay the evaluation of the branches
    until the boolean is evaluated.

    :param b:
       promised boolean value.
    :param branch_true:
       statement to execute in case of a true predicate.
    :param branch_false:
       default operation to execute in case of a false predicate.
    :returns: :py:class:`PromisedObject`
    """
    return schedule_branches(b, quote(branch_true), quote(branch_false))


@schedule
def schedule_branches(b: bool, quoted_true, quoted_false):
    """
    Helper function to choose which workflow to execute
    based on the boolean `b`.

    :param b:
       promised boolean value

    :param quoted_true:
       quoted workflow to eval if the boolean is true.
    :param quoted_true:
       quoted workflow to eval if the boolean is false.    """
    if b:
        return unquote(quoted_true)
    else:
        return unquote(quoted_false)
