from .decorator import schedule

@schedule
def gather(*a):
    """
    Converts a list of workflows (i.e. `PromisedObject`) to
    a workflow representing the promised list of values.

    Currently the `merge_workflow` function detects workflows
    only by their top type (using `isinstance`). If we have some
    deeper structure containing `PromisedObject`s, these are not
    recognised as workflow input and taken as literal values.

    This behaviour may change in the future, making this function
    `bind` obsolete.
    """
    return list(a)
