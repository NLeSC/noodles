from .datamodel import *
from queue import Queue

def run_node(node):
    return node.foo(*node.bound_args.args, **node.bound_args.kwargs)

Job = namedtuple('Job', ['workflow', 'node'])

DynamicLink = namedtuple('DynamicLink', ['source', 'target', 'node'])

def queue_workflow(Q, workflow):
    depends = invert_links(workflow.links)

    for n in workflow.nodes:
        if depends[n] == {}:
            Q.put(Job(workflow = workflow, node = n))
