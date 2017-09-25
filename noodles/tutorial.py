from inspect import Parameter
from graphviz import Digraph

from . import schedule, schedule_hint, get_workflow


# scheduled functions

@schedule
def add(x, y):
    return x + y


@schedule_hint(display="{a} + {b}", confirm=True)
def log_add(a, b):
    return a + b


@schedule
def sub(x, y):
    return x - y


@schedule
def mul(x, y):
    return x*y


@schedule
def accumulate(lst, start=0):
    return sum(lst, start)


# functions for printing workflow graphs in notebooks

def _format_arg_list(a, v):
    if len(a) == 0:
        if v:
            return "(\u2026)"
        else:
            return "()"

    s = "("
    for i in a[:-1]:
        s += str(i) if i != Parameter.empty else "\u2014"
        s += ", "

    if v:
        s += "\u2014"
    else:
        s += str(a[-1]) if a[-1] != Parameter.empty else "\u2014"

    s += ")"
    return s


def get_workflow_graph(promise):
    workflow = get_workflow(promise)

    dot = Digraph()
    for i,n in workflow.nodes.items():
        dot.node(str(i), label="{0} \n {1}".format(
            n.foo.__name__,
            _format_arg_list(n.bound_args.args, None)))

    for i in workflow.links:
        for j in workflow.links[i]:
            dot.edge(str(i), str(j[0]), label=str(j[1].name))

    return dot
