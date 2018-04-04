from ..lib import (Connection, FlushQueue, EndOfQueue)
from .job_keeper import (JobKeeper)

from ..workflow import (
    is_workflow, get_workflow, insert_result,
    Workflow, is_node_ready)
import sys


class Job:
    def __init__(self, workflow, node_id):
        self.workflow = workflow
        self.node_id = node_id

    def __iter__(self):
        return iter((self.workflow, self.node_id))

    @property
    def node(self):
        return self.workflow.nodes[self.node_id]

    @property
    def name(self):
        return self.node.foo.__name__

    @property
    def hints(self):
        return self.node.hints

    @property
    def is_root_node(self):
        return self.node_id == self.workflow.root


class DynamicLink:
    def __init__(self, source, target, node):
        self.source = source
        self.target = target
        self.node = node

    def __iter__(self):
        return iter((self.source, self.target, self.node))


error_msg_1 = \
    "A job reported an unexpected error. If this error is not so " \
    "unexpected, consider capturing it with an error handler inside " \
    "the scheduled function or with an error handler in the scheduler " \
    "for a more graceful display and exit.\n" \
    "Infringing job: \n        {}\n"


class Scheduler:
    """
    Schedules jobs, recieves results, then schedules more jobs as they
    become ready to compute. This class communicates with a pool of workers
    by means of coroutines.
    """
    def __init__(self, verbose=False, error_handler=None, job_keeper=None):
        if job_keeper is None:
            self.jobs = JobKeeper()
        else:
            self.jobs = job_keeper
        self.dynamic_links = self.jobs.workflows
        self.count = 0
        self.key_map = {}
        self.verbose = verbose
        self.handle_error = error_handler

    def run(self, connection: Connection, master: Workflow):
        """Run a workflow.

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
        errors = []

        # process results
        for job_key, status, result, err_msg in source:
            wf, n = self.jobs[job_key]
            if status == 'error':
                graceful_exit = True
                errors.append(err_msg)

                try:
                    sink.send(FlushQueue)
                except StopIteration:
                    pass

                print("Uncaught error running job: {}, {}".format(n, err_msg),
                      file=sys.stderr)
                print("Flushing queue and waiting for threads to close.",
                      file=sys.stderr, flush=True)

            if status == 'aborted':
                print("Job {} got aborted: {}".format(n, err_msg),
                      file=sys.stderr)
                print("Flushing queue and waiting for threads to close.",
                      file=sys.stderr, flush=True)
                graceful_exit = True
                errors.append(err_msg)
                try:
                    sink.send(FlushQueue)
                except StopIteration:
                    pass

            if self.verbose:
                print("sched result [{0}]: ".format(self.key_map[job_key]),
                      result,
                      file=sys.stderr, flush=True)

            del self.jobs[job_key]
            if len(self.jobs) == 0 and graceful_exit:
                for error in errors:
                    print("Exception of type", type(error), ":")
                    print(error)
                raise errors[0]

            # if this result is the root of a workflow, pop to parent
            # we do this before scheduling a child workflow, as to
            # achieve tail-call elimination.
            while n == wf.root and wf is not master:
                child = id(wf)
                _, wf, n = self.dynamic_links[child]
                del self.dynamic_links[child]

            # if we retrieve a workflow, push a child
            if is_workflow(result) and not graceful_exit:
                child_wf = get_workflow(result)
                self.add_workflow(child_wf, wf, n, sink)
                continue

            # insert the result in the nodes that need it
            wf.nodes[n].result = result
            for (tgt, address) in wf.links[n]:
                insert_result(wf.nodes[tgt], address, result)
                if is_node_ready(wf.nodes[tgt]) and not graceful_exit:
                    self.schedule(Job(workflow=wf, node_id=tgt), sink)

            # see if we're done
            if wf == master and n == master.root:
                try:
                    sink.send(EndOfQueue)
                except StopIteration:
                    pass

                return result

    def schedule(self, job, sink):
        sink.send(self.jobs.register(job))

    def add_workflow(self, wf, target, node, sink):
        self.dynamic_links[id(wf)] = DynamicLink(
            source=wf, target=target, node=node)

        for n in wf.nodes:
            if is_node_ready(wf.nodes[n]):
                self.schedule(Job(workflow=wf, node_id=n), sink)
