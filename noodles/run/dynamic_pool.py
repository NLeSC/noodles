from .queue import Queue
from .connection import Connection
from .coroutine import coroutine
from .protect import CatchExceptions
from .haploid import (push, patch)
from .worker import run_job

import xenon
import jpype

import threading
import sys
import uuid

from .xenon import (XenonScheduler)


class DynamicPool:
    def __init__(self):
        self.workers = []
        self.lock = threading.Lock()

    def add_worker(self, job_config):

def read_result(registry, s):
    obj = registry.from_json(s)
    status = obj['status']
    key = obj['key']
    try:
        key = uuid.UUID(key)
    except ValueError:
        pass

    return key, status, obj['result'], obj['err_msg']


def put_job(registry, host, key, job):
    obj = {'key': key if isinstance(key, str) else key.hex,
           'node': job}
    return registry.to_json(obj, host=host)


def xenon_interactive_worker(XeS: XenonScheduler, job_config):
    """Uses Xenon to run a single remote interactive worker.

    Jobs are read from stdin, and results written to stdout.

    :param XeS:
        The :py:class:`XenonScheduler` object that allows us to schedule the
        new worker.
    :type Xe: XenonScheduler

    :param job_config:
        Job configuration. Specifies the command to be run remotely.
    """
    cmd = job_config.command_line()
    J = XeS.submit(cmd, interactive=True)

    # status = J.wait_until_running(job_config.time_out)
    # if not status.isRunning():
    #     raise RuntimeError("Could not get the job running")
    # else:
    #     print(job_config.name + " is now running.",
    # file=sys.stderr, flush=True)

    # print(job_config.name + " is now running.", file=sys.stderr, flush=True)

    def read_stderr():
        jpype.attachThreadToJVM()
        for line in xenon.conversions.read_lines(J.streams.getStderr()):
            print(job_config.name + ": " + line, file=sys.stderr, flush=True)

    J.stderr_thread = threading.Thread(target=read_stderr)
    J.stderr_thread.daemon = True
    J.stderr_thread.start()

    registry = job_config.registry()

    @coroutine
    def send_job():
        out = xenon.conversions.OutputStream(J.streams.getStdin())

        while True:
            key, ujob = yield
            print(put_job(registry, 'scheduler', key, ujob),
                  file=out, flush=True)

    def get_result():
        """ Returns a result tuple: key, status, result, err_msg """
        for line in xenon.conversions.read_lines(J.streams.getStdout()):
            yield read_result(registry, line)

    if job_config.init is not None:
        send_job().send(("init", job_config.init()._workflow.root_node))
        key, status, result, err_msg = next(get_result())
        if key != "init" or not result:
            raise RuntimeError("The initializer function did not succeed on "
                               "worker.")

    if job_config.finish is not None:
        send_job().send(("finish", job_config.finish()._workflow.root_node))

    return Connection(get_result, send_job)


def hybrid_threaded_worker(selector, workers):
    """Runs a set of workers, each in a separate thread.

    :param selector:
        A function that takes a hints-tuple and returns a key
        indexing a worker in the `workers` dictionary.
    :param workers:
        A dictionary of workers.

    :returns:
        A connection for the scheduler.
    :rtype: Connection

    The hybrid worker dispatches jobs to the different workers
    based on the information contained in the hints. If no hints
    were given, the job is run in the main thread.

    Dispatching is done in the main thread. Retrieving results is
    done in a separate thread for each worker. In this design it is
    assumed that dispatching a job takes little time, while waiting for
    one to return a result may take a long time.
    """
    results = Queue()

    # print([w.source for k, w in workers.items()])

    catch = {
        k: CatchExceptions(results.sink)
        for k, w in workers.items()
    }

    result_source = {
        k: w.source >> catch[k].result_source
        for k, w in workers.items()
    }

    job_sink = {
        k: (catch[k].job_sink >> w.sink)()
        for k, w in workers.items()
    }

    @push
    def dispatch_job():
        default_sink = results.sink()

        while True:
            key, job = yield
            worker = selector(job)
            if worker:
                job_sink[worker].send((key, job))
            else:
                default_sink.send(run_job(key, job))

    for key, worker in workers.items():
        t = threading.Thread(
            target=catch[key](patch),
            args=(result_source[key], results.sink))
        t.daemon = True
        t.start()

        if worker.aux:
            t_aux = threading.Thread(
                target=catch[key](worker.aux),
                args=(),
                daemon=True)
            t_aux.start()

    return Connection(results.source, dispatch_job)


def buffered_dispatcher(workers):
    jobs = Queue()
    results = Queue()

    def dispatcher(source, sink):
        jpype.attachThreadToJVM()
        result_sink = results.sink()

        for job in jobs.source():
            sink.send(job)
            result_sink.send(next(source))

    for w in workers.values():
        t = threading.Thread(
            target=dispatcher,
            args=w.setup())
        t.daemon = True
        t.start()

    return Connection(results.source, jobs.sink)
