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
        if isinstance(i, float):
            istr = "{:.6}".format(i)
        else:
            istr = str(i)

        s = s.format(
            _sugar(istr)
            if i is not Parameter.empty
            else "\u2014", ", {0}{1}")

    if v:
        return s.format("\u2026", "")

    if isinstance(a[-1], float):
        istr = "{:.6}".format(a[-1])
    else:
        istr = str(a[-1])

    return s.format(
        _sugar(istr)
        if a[-1] is not Parameter.empty
        else "\u2014", "")


def draw_workflow(filename, workflow, paint=None):
    dot = AGraph(directed=True)  # (comment="Computing scheme")
    dot.node_attr['style'] = 'filled'
    for i, n in workflow.nodes.items():
        dot.add_node(i, label="{0} \n {1}".format(
            n.foo.__name__, _format_arg_list(n.bound_args.args, None)))
        x = dot.get_node(i)
        if paint:
            paint(x, n.foo.__name__)

    for i in workflow.links:
        for j in workflow.links[i]:
            dot.add_edge(i, j[0])
    dot.layout(prog='dot')

    dot.draw(filename)


def graph(workflow):
    dot = AGraph(directed=True)  # (comment="Computing scheme")
    for i, n in workflow.nodes.items():
        dot.add_node(i, label="{0} \n {1}".format(
            n.foo.__name__, _format_arg_list(n.bound_args.args, None)))

    for i in workflow.links:
        for j in workflow.links[i]:
            dot.add_edge(i, j[0])
    dot.layout(prog='dot')
    return dot
