"""
Functions useful for tutorial work and unit testing.
"""

from inspect import Parameter
from graphviz import Digraph

from . import schedule, schedule_hint, get_workflow


@schedule
def add(x, y):
    """(schedule) add `x` and `y`."""
    return x + y


@schedule_hint(display="{a} + {b}", confirm=True)
def log_add(a, b):
    """(scheduled) add `a` and `b` and send message to logger."""
    return a + b


@schedule
def sub(x, y):
    """(scheduled) subtract `y` from `x`."""
    return x - y


@schedule
def mul(x, y):
    """(scheduled) multiply `x` and `y`."""
    return x*y


@schedule
def accumulate(lst, start=0):
    """(scheduled) compute sum of `lst`."""
    return sum(lst, start)


def _format_arg_list(args, variadic=False):
    """Format a list of arguments for pretty printing.

    :param a: list of arguments.
    :type a: list

    :param v: tell if the function accepts variadic arguments
    :type v: bool
    """
    if not args:
        if variadic:
            return "(\u2026)"
        else:
            return "()"

    result = "("
    for arg in args[:-1]:
        result += str(arg) if arg != Parameter.empty else "\u2014"
        result += ", "

    if variadic:
        result += "\u2014"
    else:
        result += str(args[-1]) if args[-1] != Parameter.empty else "\u2014"

    result += ")"
    return result


def get_workflow_graph(promise):
    """Get a graph of a promise."""
    workflow = get_workflow(promise)

    dot = Digraph()
    for i, n in workflow.nodes.items():
        dot.node(str(i), label="{0} \n {1}".format(
            n.foo.__name__,
            _format_arg_list(n.bound_args.args)))

    for i in workflow.links:
        for j in workflow.links[i]:
            dot.edge(str(i), str(j[0]), label=str(j[1].name))

    return dot
