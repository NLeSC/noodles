from .coroutines import coroutine_sink, Connection
from .data_json import saucer, desaucer, node_to_jobject
from .logger import log
from .run_hybrid import hybrid_threaded_worker
from .run_common import Scheduler
from .datamodel import get_workflow

import threading
from subprocess import Popen, PIPE
import json
import uuid
import random

def read_result(s):
    obj = json.loads(s, object_hook=desaucer())
    key = obj['key']
    try:
        key = uuid.UUID(key)
    except ValueError:
        pass

    return key, obj['result']


def put_job(host, key, job):
    obj = {'key': key if isinstance(key, str) else key.hex,
           'node': node_to_jobject(job.node())}
    return json.dumps(obj, default=saucer(host))

# processes = {}


def process_worker(verbose=False, jobdirs=False, init=None, finish=None):
    name = "process-" + str(uuid.uuid4())

    cmd = ["python3.5", "-m", "noodles.worker", "online", "-name", name]
    if verbose:
        cmd.append("-verbose")
    if jobdirs:
        cmd.append("-jobdirs")
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
        while True:
            key, job = yield
            print(put_job(name, key, job), file=p.stdin, flush=True)

    def get_result():
        for line in p.stdout:
            key, result = read_result(line)
            yield (key, result)

    if init is not None:
        send_job().send(("init", init()._workflow.root_node))
        key, result = next(get_result())
        if key != "init" or not result:
            raise RuntimeError("The initializer function did not succeed on worker.")

    if finish is not None:
        send_job().send(("finish", finish()._workflow.root_node))

    return Connection(get_result, send_job, name=name)


def run_process(wf, n_processes,
                verbose=False, jobdirs=False, init=None, finish=None):
    """Run the workflow using a number of new python processes. Use this
    runner to test the workflow in a situation where data serialisation
    is needed.

    :param wf:
        The workflow.
    :type wf: `Workflow` or `PromisedObject`

    :param n_processes:
        Number of processes to start.

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
        new_worker = process_worker(verbose, jobdirs, init, finish)
        workers[new_worker.name] = new_worker

    worker_names = list(workers.keys())
    def random_selector(job):
        return random.choice(worker_names)

    master_worker = hybrid_threaded_worker(random_selector, workers)
    return Scheduler().run(master_worker, get_workflow(wf))