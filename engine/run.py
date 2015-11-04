from .datamodel import *

def run_node(node):
    return node.foo(*node.bound_args.args, **node.bound_args.kwargs)

from queue import Queue

def run(workflow):
    workflow = get_workflow(workflow)
    if not workflow:
        raise RuntimeError("Argument is not a workflow.")

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

        if is_workflow(v):
            substitute_node(workflow, n, v)

        results[n] = v

        for (tgt, address) in workflow.links[n]:
            insert_result(workflow.nodes[tgt], address, v)
            if is_node_ready(workflow.nodes[tgt]):
                q.put(tgt)

    return results[workflow.top]
