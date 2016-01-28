from noodles.data_types import is_workflow, get_workflow, Empty
from noodles.data_graph import invert_links
from noodles.datamodel import insert_result, is_node_ready
from collections import namedtuple
import uuid
import sys


def run_job(node):
    return node.foo(*node.bound_args.args, **node.bound_args.kwargs)


# def get_hints(node):
#     return node.hints

Job = namedtuple('Job', ['workflow', 'node'])

DynamicLink = namedtuple('DynamicLink', ['source', 'target', 'node'])


class Scheduler:
    """
    Schedules jobs, recieves results, then schedules more jobs as they
    become ready to compute. This class communicates with a pool of workers
    by means of coroutines.
    """
    def __init__(self, verbose=False):
        self.dynamic_links = {}
        self.results = {}
        self.jobs = {}
        self.count = 0
        self.key_map = {}
        self.verbose = verbose

    def run(self, connection, master):
        """
        Run a workflow.

        :param connection:
            A connection giving a sink to the job-queue and a source yielding
            results.
        :type connection: Connection

        :param master:
            The workflow.
        :type master: Workflow
        """
        # initiate worker slave army and take up reins ...
        source, sink = connection.setup()

        # schedule work
        self.add_workflow(master, master, master.root, sink)

        # process results
        for job_key, result in source:
            if self.verbose:
                print("sched result [{0}]: ".format(self.key_map[job_key]),
                      result,
                      file=sys.stderr, flush=True)
            wf, n = self.jobs[job_key]

            # if we retrieve a workflow, push a child
            if is_workflow(result):
                child_wf = get_workflow(result)
                self.add_workflow(child_wf, wf, n, sink)
                continue

            # if this result is the root of a workflow, pop to parent
            if n == wf.root:
                _, wf, n = self.dynamic_links[id(wf)]

            # save the result
            self.results[id(wf)][n] = result

            # and insert it in the nodes that need it
            for (tgt, address) in wf.links[n]:
                insert_result(wf.nodes[tgt], address, result)
                if is_node_ready(wf.nodes[tgt]):
                    self.schedule(Job(workflow=wf, node=tgt), sink)

            # see if we're done
            if wf == master and n == master.root:
                return result

        print("Seventh circle of HELL")

    def schedule(self, job, sink):
        uid = uuid.uuid1()
        self.jobs[uid] = job
        self.count += 1
        self.key_map[uid] = self.count
        node = job.workflow.nodes[job.node]
        if self.verbose:
            print("sched job [{0}]: ".format(self.count),
                  node.foo.__name__, node.bound_args.args,
                  file=sys.stderr, flush=True)
        sink.send((uid, node))
        return uid

    def add_workflow(self, wf, target, node, sink):
        self.dynamic_links[id(wf)] = DynamicLink(
            source=wf, target=target, node=node)

        self.results[id(wf)] = dict((n, Empty) for n in wf.nodes)

        depends = invert_links(wf.links)

        for n in wf.nodes:
            if depends[n] == {}:
                self.schedule(Job(workflow=wf, node=n), sink)
