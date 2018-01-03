import functools


def decorator(f):
    """Creates a paramatric decorator from a function. The resulting decorator
    will optionally take keyword arguments."""
    @functools.wraps(f)
    def decoratored_function(*args, **kwargs):
        if args and len(args) == 1:
            return f(*args, **kwargs)

        if args:
            raise TypeError(
                "This decorator only accepts extra keyword arguments.")

        return lambda g: f(g, **kwargs)

    return decoratored_function
