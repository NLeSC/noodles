import sys
import threading
import uuid
from subprocess import Popen, PIPE

import os
import random
from noodles.datamodel import get_workflow
from noodles.logger import log
from noodles.run.coroutines import coroutine_sink, Connection
from noodles.serial.registry import RefObject
from noodles.utility import object_name
from .scheduler import Scheduler
from .hybrid import hybrid_threaded_worker


def read_result(registry, s):
    obj = registry.from_json(s)
    key = obj['key']
    status = obj['status']

    try:
        key = uuid.UUID(key)
    except ValueError:
        pass

    return key, status, obj['result']


def put_job(registry, host, key, job):
    obj = {'key': key if isinstance(key, str) else key.hex,
           'node': job}
    return registry.to_json(obj, host=host)


def process_worker(registry,
                   verbose=False, jobdirs=False,
                   init=None, finish=None, status=True):
    name = "process-" + str(uuid.uuid4())

    cmd = ["/bin/bash", os.getcwd() + "/worker.sh", sys.prefix, "online",
           "-name", name, "-registry", object_name(registry)]
    if verbose:
        cmd.append("-verbose")
    if jobdirs:
        cmd.append("-jobdirs")
    if not status:
        cmd.append("-nostatus")
    if init:
        cmd.append("-init")
    if finish:
        cmd.append("-finish")

    p = Popen(
        cmd,
        stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def read_stderr():
        for line in p.stderr:
            log.worker_stderr(name, line)

    t = threading.Thread(target=read_stderr)
    t.daemon = True
    t.start()

#    processes[id(p)] = t

    @coroutine_sink
    def send_job():
        reg = registry()
        while True:
            key, job = yield
            print(put_job(reg, name, key, job), file=p.stdin, flush=True)

    def get_result():
        reg = registry()
        for line in p.stdout:
            key, status, result = read_result(reg, line)
            yield (key, status, result)

    if init is not None:
        send_job().send(("init", init()._workflow.root_node))
        key, status, result = next(get_result())
        if key != "init" or not result:
            raise RuntimeError("The initializer function did not succeed on worker.")

    if finish is not None:
        send_job().send(("finish", finish()._workflow.root_node))

    return Connection(get_result, send_job, name=name)


def run_process(wf, n_processes, registry,
                verbose=False, jobdirs=False, init=None, finish=None):
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
        Create a new directory for each job to prevent filename collision. (NYI)

    :param init:
        An init function that needs to be run in each process before other jobs
        can be run. This should be a scheduled function returning True on success.

    :param finish:
        A function that wraps up when the worker closes down.

    :returns: the result of evaluating the workflow
    :rtype: any
    """
    workers = {}
    for i in range(n_processes):
        new_worker = process_worker(registry, verbose, jobdirs, init, finish)
        workers[new_worker.name] = new_worker

    worker_names = list(workers.keys())

    def random_selector(job):
        return random.choice(worker_names)

    master_worker = hybrid_threaded_worker(random_selector, workers)
    result = Scheduler().run(master_worker, get_workflow(wf))

    if isinstance(result, RefObject):
        return registry().decode(result.rec, deref=True)
    else:
        return result
