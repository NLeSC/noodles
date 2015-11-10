from .run_common import *
import threading

def run_parallel(workflow, n_threads):
    """
    Runs a workflow in parallel using a Queue scheme. Each node that
    is ready for computation is added to the queue. When a worker finishes
    it puts the answer into the target nodes, and checks each of these nodes
    for readiness. If the workflow doesn't contain any bugs (a dangerous
    assumption!), each argument of a node has only one source.
    There is only one thread that will find a node ready with the last value
    inserted, but we do need to lock when checking for readiness. For this we
    create a lock for each node in the workflow.

    :param workflow:
        the workflow
    :type workflow: Workflow

    :param n_threads:
        number of threads
    :type n_threads: int

    :returns: output of workflow
    :rtype: Any
    """
    master = get_workflow(workflow)
    if not master:
        raise RuntimeError("Argument is not a workflow.")

    global_lock = threading.Lock()

    locks   = {
        id(master):
            dict((n, threading.Lock()) for n in master.nodes)
    }

    dynamic_links = {
        id(master):
            DynamicLink(source = master, target = master, node = master.root)
    }

    results = {
        id(master):
            dict((n, Empty) for n in master.nodes)
    }

    Q = Queue()
    queue_workflow(Q, master)

    if Q.empty():
        raise RuntimeError("No node is ready for execution, " \
                           "emtpy workflow or circular dependency.")

    def worker():
        while True:
            w, n = Q.get()
            v = run_node(w.nodes[n])

            if is_workflow(v):
                v = get_workflow(v)

                with global_lock:
                    # if a lot of workers get nodes that evaluate to nested
                    # workflows, this may become a bottleneck
                    locks[id(v)] = dict((n, threading.Lock())
                        for n in v.nodes)

                    dynamic_links[id(v)] = DynamicLink(
                        source = v, target = w, node = n)

                    results[id(v)] = dict((n, Empty)
                        for n in v.nodes)

                queue_workflow(Q, v) # Queue is already thread-safe

                Q.task_done()
                continue

            if n == w.root:
                _, w, n = dynamic_links[id(w)]

            results[id(w)][n] = v

            for (tgt, address) in w.links[n]:
                with locks[id(w)][tgt]:
                    # even though we're writing to unique locations, the
                    # insert_result function is not thread safe.
                    # I don't know why.
                    insert_result(w.nodes[tgt], address, v)

                    if is_node_ready(w.nodes[tgt]):
                        Q.put(Job(workflow = w, node = tgt))

            Q.task_done()

    for i in range(n_threads):
        t = threading.Thread(target = worker)
        t.daemon = True
        t.start()

    Q.join()

    return results[id(master)][master.root]
