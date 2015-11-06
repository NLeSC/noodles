from .run_common import *

def run(workflow):
    """
    Returns the result of evaluting the worflow
    :param workflow:  Workflow to compute
    :type  workflow: namedTuple |Workflow| or |PromisedObject| 
    
    """
    master = get_workflow(workflow)
    if not master:
        raise RuntimeError("Argument is not a workflow.")

    results = dict((n, Empty) for n in master.nodes)
    dynamic_links = { id(master): DynamicLink(
        source = master, target = master, node = master.top) }

    Q = Queue()
    queue_workflow(Q, master)

    if Q.empty():
        raise RuntimeError("No node is ready for execution, " \
                           "emtpy workflow or circular dependency.")

    while not Q.empty():
        w, n = Q.get()
        v = run_node(w.nodes[n])

        if is_workflow(v):
            v = get_workflow(v)
            dynamic_links[id(v)] = DynamicLink(
                source = v, target = w, node = n)
            queue_workflow(Q, v)
            continue

        if n == w.top:
            _, w, n = dynamic_links[id(w)]

        results[n] = v

        for (tgt, address) in w.links[n]:
            insert_result(w.nodes[tgt], address, v)
            if is_node_ready(w.nodes[tgt]):
                Q.put(Job(workflow = w, node = tgt))

    return results[master.top]
