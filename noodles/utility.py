from .decorator import schedule

@schedule
def gather(*a):
    """
    Converts a list of workflows (i.e. :py:class:`PromisedObject`) to
    a workflow representing the promised list of values.

    Currently the :py:func:`from_call` function detects workflows
    only by their top type (using `isinstance`). If we have some
    deeper structure containing :py:class:`PromisedObject`, these are not
    recognised as workflow input and taken as literal values.

    This behaviour may change in the future, making this function
    `gather` obsolete.
    """
    return list(a)
