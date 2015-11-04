from .datamodel import *

def run_node(node):
    return node.foo(*node.bound_args.args, **node.bound_args.kwargs)

from queue import Queue

Job = namedtuple('Job', ['workflow', 'node'])

DynamicLink = namedtuple('DynamicLink', ['source', 'target', 'node'])

def queue_workflow(Q, workflow):
    depends = invert_links(workflow.links)

    for n in workflow.nodes:
        if depends[n] == {}:
            Q.put(Job(workflow = workflow, node = n))

def run(workflow):
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
