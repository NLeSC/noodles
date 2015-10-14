################################################################################
# Drawing routines                                                             |
#------------------------------------------------------------------------------+
from pygraphviz import AGraph

def _format_arg_list(a, v):
    if len(a) == 0: 
        if v:
            return "(\u2026)"
        else:
            return "()"    
            
    s = "({0}{1})"
    for i in a[:-1]:
        s = s.format(str(i), ", {0}{1}")
        
    if v:
        return s.format("\u2026", "")
        
    return s.format(str(a[-1]), "")

def draw_workflow(fn, workflow):
    #sr = simplify_runner(runner)
    sr = workflow
    dot = AGraph(directed=True) #(comment="Computing scheme")
    for i,n in sr.nodes.items():
        dot.add_node(i, label="{0} \n {1}".format(n.foo.__name__, 
            _format_arg_list(n.args, n.varargs)))
        
    for i in sr.links:
        for j in sr.links[i]:
            dot.add_edge(i, j[0])
    dot.layout(prog='dot')

    dot.draw(fn)

