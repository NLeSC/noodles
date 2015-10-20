from .datamodel import *

def run_node(node):
    return node.foo(*node.bound_args.args, **node.bound_args.kwargs)

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
        
        for (tgt, address) in workflow.links[n]:
            insert_result(workflow.nodes[tgt], address, v)
            if is_node_ready(workflow.nodes[tgt]):
                q.put(tgt)
    
    return results[workflow.top]

import threading

def run_parallel(workflow, n_threads):
    """
    Runs a workflow in parallel using a simple Queue scheme. Each node that
    is ready for computation is added to the queue. When a worker finishes
    it puts the answer into the target nodes, and checks each of these nodes
    for readiness. If the workflow doesn't contain any bugs (a dangerous
    assumption!), each argument of a node has only one source. 
    There is only one thread that will find a node ready with the last value
    inserted, but we do need to lock when checking for readiness. For this we
    create a lock for each node in the workflow.
    
    @param workflow:
        the workflow
    @type workflow: Workflow
    
    @param n_threads:
        number of threads
    @type n_threads: int
    
    @returns: output of workflow
    @rtype: Any
    """
    locks   = dict((n, threading.Lock()) for n in workflow.nodes)
    results = dict((n, Empty) for n in workflow.nodes)
    depends = invert_links(workflow.links)

    q = Queue()
    for n in workflow.nodes:
        if depends[n] == {}:
            q.put(n)
    
    if q.empty():
        raise RuntimeError("No node is ready for execution, " \
                             "emtpy workflow or circular dependency.")
    
    def worker():
        while True:
            n = q.get()
            v = run_node(workflow.nodes[n])
            results[n] = v
            
            for (tgt, address) in workflow.links[n]:
                insert_result(workflow.nodes[tgt], address, v)
                
                locks[tgt].acquire()
                if is_node_ready(workflow.nodes[tgt]):
                    q.put(tgt)
                locks[tgt].release()
            
            q.task_done()
    
    for i in range(n_threads):
        t = threading.Thread(target = worker)
        t.daemon = True
        t.start()
        
    q.join()
    
    return results[workflow.top]
    
