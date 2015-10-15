from .datamodel import *

def run_node(node):
    return node.foo(*(node.args + node.varargs), **node.keywords)

def insert_result(node, arg_type, pos, value):
    """
    Modifies a node by inserting the value at the specified position
    in the argument specification of the node. Returns True if the node
    is ready for evaluation, False otherwise.
    """
    spec = inspect.getargspec(node.foo)
    
    if   arg_type == ArgumentType.regular:
        i = spec.args.index(pos)
        if node.args[i] != Empty:
            raise RuntimeError("Noodle panic. Argument {arg} in " \
                                 "{name} already given." \
                   .format(arg=pos, name=node.foo.__name__))
            
        node.args[i] = value
    
    elif arg_type == ArgumentType.variadic:
        if node.varargs[pos] != Empty:
            raise RuntimeError("Noodle panic. Variadic argument no. " \
                                 "{n} in {name} already given." \
                   .format(n=pos, name=node.foo.__name__))
                   
        node.varargs[pos] = value
        
    else: # keyword argument
        if node.keywords[pos] != Empty:
            raise RuntimeError("Noodle panic. Keyword argument {arg} in " \
                                 "{name} already given." \
                   .format(arg=pos, name=node.foo.__name__))
                   
        node.keywords[pos] = value
        
    return is_node_ready(node)

from queue import Queue
                
def run(workflow):
    results = dict((n, Empty) for n in workflow.nodes)
    depends = invert_links(workflow.links)
    
    q = Queue()
    for n in workflow.nodes:
        if depends[n] == {}:
            q.put(n)
    
    if q.empty():
        raise RuntimeError("No node is ready for execution, " \
                             "emtpy workflow or circular dependency.")
    
    while not q.empty():
        n = q.get()
        v = run_node(workflow.nodes[n])
        results[n] = v
        
        for (tgt, arg_type, pos) in workflow.links[n]:
            if insert_result(workflow.nodes[tgt], arg_type, pos, v):
                q.put(tgt)
    
    return results[workflow.top]
        
    
    
    
