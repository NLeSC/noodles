from .connection import (Connection)
from .job_keeper import (JobKeeper)

from ..workflow import (
    is_workflow, get_workflow, insert_result,
    is_node_ready, Workflow)
from ..interface import (JobException)
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
        # I'd rather say: self.jobs = job_keeper or {}
        # but Python thruthiness of {} is False
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

        # process results
        for job_key, status, result, err_msg in source:
            if status == 'aborted':
                print("Got a fatal error: exiting.",
                      file=sys.stderr, flush=True)
                sys.exit()

            wf, n = self.jobs[job_key]
            if status == 'error':
                if self.handle_error and isinstance(err_msg, JobException):
                    if self.handle_error(wf.nodes[n], *err_msg):
                        graceful_exit = True
                    else:
                        err_msg.reraise()

                else:
                    if isinstance(err_msg, JobException):
                        err_msg.reraise()
                    elif isinstance(err_msg, Exception):
                        raise err_msg
                    else:
                        raise RuntimeError(
                            error_msg_1.format(wf.nodes[n]) + "\n"
                            "Exception raised: {}".format(err_msg))

            if self.verbose:
                print("sched result [{0}]: ".format(self.key_map[job_key]),
                      result,
                      file=sys.stderr, flush=True)

            del self.jobs[job_key]
            if len(self.jobs) == 0 and graceful_exit:
                return

            # if this result is the root of a workflow, pop to parent
            # we do this before scheduling a child workflow, as to
            # achieve tail-call elimination.
            while n == wf.root and wf is not master:
                child = id(wf)
                _, wf, n = self.dynamic_links[child]
                del self.dynamic_links[child]

            # if we retrieve a workflow, push a child
            if is_workflow(result):
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
                return result

        print("Seventh circle of HELL")

    def schedule(self, job, sink):
        sink.send(self.jobs.register(job))

    def add_workflow(self, wf, target, node, sink):
        self.dynamic_links[id(wf)] = DynamicLink(
            source=wf, target=target, node=node)

        for n in wf.nodes:
            if is_node_ready(wf.nodes[n]):
                self.schedule(Job(workflow=wf, node_id=n), sink)
