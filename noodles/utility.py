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

def map_dict(f, d):
    return dict((k, f(v)) for k, v in d.items())

def unzip_dict(d):
    a = {}
    b = {}

    for k, (v, w) in d.items():
        a[k] = v
        b[k] = w

    return a, b
