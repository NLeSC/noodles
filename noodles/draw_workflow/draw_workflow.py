from pygraphviz import AGraph
from inspect import Parameter


def _sugar(s):
    s = s.replace("{", "{{").replace("}", "}}")
    if len(s) > 50:
        return s[:20] + " ... " + s[-20:]
    else:
        return s


def _format_arg_list(a, v):
    if len(a) == 0:
        if v:
            return "(\u2026)"
        else:
            return "()"

    s = "({0}{1})"
    for i in a[:-1]:
        s = s.format(
            _sugar(str(i))
            if i != Parameter.empty
            else "\u2014", ", {0}{1}")

    if v:
        return s.format("\u2026", "")

    return s.format(
        _sugar(str(a[-1]))
        if a[-1] != Parameter.empty
        else "\u2014", "")


def draw_workflow(filename, workflow):
    dot = AGraph(directed=True)  # (comment="Computing scheme")
    for i, n in workflow.nodes.items():
        dot.add_node(i, label="{0} \n {1}".format(
            n.foo.__name__, _format_arg_list(n.bound_args.args, None)))

    for i in workflow.links:
        for j in workflow.links[i]:
            dot.add_edge(i, j[0])
    dot.layout(prog='dot')

    dot.draw(filename)
