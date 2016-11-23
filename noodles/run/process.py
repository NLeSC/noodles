import sys
import uuid
from subprocess import Popen, PIPE
import threading

import os
import random
from ..workflow import get_workflow
# from ..logger import log
from .connection import Connection
from ..utility import object_name
from .scheduler import Scheduler
# from .protect import CatchExceptions
from .hybrid import hybrid_threaded_worker
from .haploid import (pull, push)

from .remote.io import (
    MsgPackObjectReader, MsgPackObjectWriter,
    JSONObjectReader, JSONObjectWriter)

try:
    import msgpack  # noqa
    has_msgpack = True
except ImportError:
    has_msgpack = False


def process_worker(registry, verbose=False, jobdirs=False,
                   init=None, finish=None, status=True, use_msgpack=False):
    name = "process-" + str(uuid.uuid4())

    cmd = ["/bin/bash", os.getcwd() + "/worker.sh", sys.prefix, "online",
           "-name", name, "-registry", object_name(registry)]
    if use_msgpack:
        assert has_msgpack
        cmd.append("-msgpack")
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

    p = Popen(
        cmd,
        stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def read_stderr():
        for line in p.stderr:
            print(name + ": " + line.strip(), file=sys.stderr, flush=True)

    t = threading.Thread(target=read_stderr)
    t.daemon = True
    t.start()

    @push
    def send_job():
        reg = registry()
        if use_msgpack:
            yield from MsgPackObjectWriter(reg, p.stdin.buffer)
        else:
            yield from JSONObjectWriter(reg, p.stdin)

    @pull
    def get_result():
        reg = registry()
        if use_msgpack:
            newin = os.fdopen(p.stdout.fileno(), 'rb', buffering=0)
            yield from MsgPackObjectReader(reg, newin)
        else:
            yield from JSONObjectReader(reg, p.stdout)

    return Connection(get_result, send_job, aux=read_stderr)


def run_process(wf, n_processes, registry,
                verbose=False, jobdirs=False,
                init=None, finish=None, deref=False, use_msgpack=False):
    """Run the workflow using a number of new python processes. Use this
    runner to test the workflow in a situation where data serial
    is needed.

    :param wf:
        The workflow.
    :type wf: `Workflow` or `PromisedObject`

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
        new_worker = process_worker(registry, verbose, jobdirs, init, finish,
                                    use_msgpack=use_msgpack)
        workers['worker {0:2}'.format(i)] = new_worker

    worker_names = list(workers.keys())

    def random_selector(job):
        return random.choice(worker_names)

    master_worker = hybrid_threaded_worker(random_selector, workers)
    result = Scheduler().run(master_worker, get_workflow(wf))

    if deref:
        return registry().dereference(result, host='localhost')
    else:
        return result
