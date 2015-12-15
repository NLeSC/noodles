from .datamodel import get_workflow
from .run_common import run_job, Scheduler
from .coroutines import IOQueue, Connection, patch, coroutine_sink
from .utility import map_dict, unzip_dict

import threading


def hybrid_coroutine_worker(selector, workers):
    """
    Runs a set of workers, all of them in the main thread.
    This runner is here for testing purposes.
    """
    jobs = IOQueue()

    worker_source, worker_sink = unzip_dict(
        map_dict(lambda w: w.setup(), workers))

    def get_result():
        source = jobs.source()

        for key, job in source:
            if job.hints is None:
                yield (key, run_job(job))
            else:
                worker = selector(job.hints)
                # send the worker a job and wait for it to return
                worker_sink[worker].send((key, job))
                result = next(worker_source[worker])
                yield result

    return Connection(get_result, jobs.sink)


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
    results = IOQueue()

    worker_source, worker_sink = unzip_dict(
        map_dict(lambda w: w.setup(), workers))

    @coroutine_sink
    def dispatch_job():
        default_sink = results.sink()

        while True:
            key, job = yield
            if job.hints:
                worker = selector(job.hints)
                worker_sink[worker].send((key, job))
            else:
                result = run_job(job)
                default_sink.send((key, result))

    for k, source in worker_source.items():
        t = threading.Thread(
            target=patch,
            args=(source, results.sink()))
        t.daemon = True
        t.start()

    return Connection(results.source, dispatch_job)


def run_hybrid(wf, selector, workers):
    """
    Returns the result of evaluating the workflow; runs through several
    supplied workers in as many threads.

    :param workflow:
        Workflow to compute
    :type workflow: :py:class:`Workflow` or :py:class:`PromisedObject`

    :param selector:
        A function selecting the worker that should be run, given a hint.
    :param workers:
        A dictionary of workers

    :returns:
        result of running the workflow
    """
    worker = hybrid_threaded_worker(selector, workers)
    return Scheduler().run(worker, get_workflow(wf))