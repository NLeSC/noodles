################################################################################
# Drawing routines                                                             |
#------------------------------------------------------------------------------+
from pygraphviz import AGraph
from inspect import Parameter



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

def draw_workflow(filename, workflow):
    dot = AGraph(directed=True, strict=False) #(comment="Computing scheme")
    for i,n in workflow.nodes.items():
        dot.add_node(i, label="{0} \n {1}".format(n.foo.__name__,
            _format_arg_list(n.bound_args.args, None)))

    for i in workflow.links:
        for j in workflow.links[i]:
            dot.add_edge(i, j[0], j[1].name) #, headlabel=j[1].name, labeldistance=1.8)
    dot.layout(prog='dot')

    dot.draw(filename)
