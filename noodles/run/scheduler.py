from noodles.workflow import (
    is_workflow, get_workflow, Empty, invert_links, insert_result,
    is_node_ready)
import uuid
import sys


def run_job(node):
    return node.foo(*node.bound_args.args, **node.bound_args.kwargs)


class Job:
    def __init__(self, workflow, node):
        self.workflow = workflow
        self.node = node

    def __iter__(self):
        return iter((self.workflow, self.node))


class DynamicLink:
    def __init__(self, source, target, node):
        self.source = source
        self.target = target
        self.node = node

    def __iter__(self):
        return iter((self.source, self.target, self.node))


class Scheduler:
    """
    Schedules jobs, recieves results, then schedules more jobs as they
    become ready to compute. This class communicates with a pool of workers
    by means of coroutines.
    """
    def __init__(self, verbose=False, error_handler=None):
        self.dynamic_links = {}
        self.results = {}
        self.jobs = {}
        self.count = 0
        self.key_map = {}
        self.verbose = verbose
        self.handle_error = error_handler

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
        graceful_exit = False

        # process results
        for job_key, status, result in source:
            if status == 'error':
                if self.handle_error:
                    wf, n = self.jobs[job_key]
                    self.handle_error(wf.nodes[n], result)
                    graceful_exit = True
                else:
                    raise result

            if self.verbose:
                print("sched result [{0}]: ".format(self.key_map[job_key]),
                      result,
                      file=sys.stderr, flush=True)
            wf, n = self.jobs[job_key]

            del self.jobs[job_key]
            if len(self.jobs) == 0 and graceful_exit:
                return

            # if we retrieve a workflow, push a child
            if is_workflow(result):
                child_wf = get_workflow(result)
                self.add_workflow(child_wf, wf, n, sink)
                continue

            # if this result is the root of a workflow, pop to parent
            while n == wf.root:
                _, wf, n = self.dynamic_links[id(wf)]
                if wf == master and n == master.root:
                    return result

            # save the result
            self.results[id(wf)][n] = result

            # and insert it in the nodes that need it
            for (tgt, address) in wf.links[n]:
                insert_result(wf.nodes[tgt], address, result)
                if is_node_ready(wf.nodes[tgt]) and not graceful_exit:
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
