"""
Process backend
===============

Run jobs using a process backend.
"""

import sys
import uuid
from subprocess import Popen, PIPE
import threading
# import logging

import random
from ..workflow import get_workflow
# from ..logger import log
from .scheduler import Scheduler
# from .protect import CatchExceptions
from .hybrid import hybrid_threaded_worker

from ..lib import (pull, push, Connection, object_name, EndOfQueue, FlushQueue)
from .messages import (EndOfWork)

from .remote.io import (JSONObjectReader, JSONObjectWriter)


def process_worker(registry, verbose=False, jobdirs=False,
                   init=None, finish=None, status=True):
    """Process worker"""
    name = "process-" + str(uuid.uuid4())

    cmd = [sys.prefix + "/bin/python", "-m", "noodles.pilot_job",
           "-name", name, "-registry", object_name(registry)]
    if verbose:
        cmd.append("-verbose")
    if jobdirs:
        cmd.append("-jobdirs")
    if not status:
        cmd.append("-nostatus")
    if init:
        cmd.extend(["-init", object_name(init)])
    if finish:
        cmd.extend(["-finish", object_name(finish)])

    remote = Popen(
        cmd,
        stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def read_stderr():
        """Read stderr of remote process and sends lines to logger."""
        for line in remote.stderr:
            print(name + ": " + line.rstrip())

    stderr_reader_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_reader_thread.start()

    @push
    def send_job():
        """Coroutine, sends jobs to remote worker over standard input."""
        reg = registry()

        sink = JSONObjectWriter(reg, remote.stdin)

        while True:
            msg = yield
            if msg is EndOfQueue:
                try:
                    sink.send(EndOfWork)
                except StopIteration:
                    pass

                remote.wait()
                stderr_reader_thread.join()

                return

            if msg is FlushQueue:
                continue

            sink.send(msg)

    @pull
    def get_result():
        """Generator, reading results from process standard output."""
        reg = registry()
        yield from JSONObjectReader(reg, remote.stdout)

    return Connection(get_result, send_job)


def run_process(workflow, *, n_processes, registry,
                verbose=False, jobdirs=False,
                init=None, finish=None, deref=False):
    """Run the workflow using a number of new python processes. Use this
    runner to test the workflow in a situation where data serial
    is needed.

    :param workflow:
        The workflow.
    :type workflow: `Workflow` or `PromisedObject`

    :param n_processes:
        Number of processes to start.

    :param registry:
        The serial registry.

    :param verbose:
        Request verbose output on worker side

    :param jobdirs:
        Create a new directory for each job to prevent filename collision.(NYI)

    :param init:
        An init function that needs to be run in each process before other jobs
        can be run. This should be a scheduled function returning True on
        success.

    :param finish:
        A function that wraps up when the worker closes down.

    :param deref:
        Set this to True to pass the result through one more encoding and
        decoding step with object derefencing turned on.
    :type deref: bool

    :returns: the result of evaluating the workflow
    :rtype: any
    """
    workers = {}
    for i in range(n_processes):
        new_worker = process_worker(registry, verbose, jobdirs, init, finish)
        workers['worker {0:2}'.format(i)] = new_worker

    worker_names = list(workers.keys())

    def random_selector(_):
        """Selects a worker to send a job to at random."""
        return random.choice(worker_names)

    master_worker = hybrid_threaded_worker(random_selector, workers)
    result = Scheduler().run(master_worker, get_workflow(workflow))

    for worker in workers.values():
        try:
            worker.sink().send(EndOfQueue)
        except StopIteration:
            pass

#        w.aux.join()

    if deref:
        return registry().dereference(result, host='localhost')
    else:
        return result
