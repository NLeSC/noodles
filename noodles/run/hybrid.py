import threading

from ..workflow import get_workflow
from ..lib import Queue, Connection, push, patch, EndOfQueue, FlushQueue
from .scheduler import Scheduler
from .worker import run_job


def hybrid_coroutine_worker(selector, workers):
    """Runs a set of workers, all of them in the main thread.
    This runner is here for testing purposes.

    :param selector:
        A function returning a worker key, given a job.
    :type selector: function

    :param workers:
        A dict of workers.
    :type workers: dict
    """
    jobs = Queue()

    worker_source = {}
    worker_sink = {}

    for k, w in workers.items():
        worker_source[k], worker_sink[k] = w.setup()

    def get_result():
        source = jobs.source()

        for msg in source:
            key, job = msg
            worker = selector(job)
            if worker is None:
                yield run_job(key, job)
            else:
                # send the worker a job and wait for it to return
                worker_sink[worker].send(msg)
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
    result_queue = Queue()

    job_sink = {k: w.sink() for k, w in workers.items()}

    @push
    def dispatch_job():
        default_sink = result_queue.sink()

        while True:
            msg = yield

            if msg is EndOfQueue:
                for k in workers.keys():
                    try:
                        job_sink[k].send(EndOfQueue)
                    except StopIteration:
                        pass
                return

            if msg is FlushQueue:
                for k in workers.keys():
                    try:
                        job_sink[k].send(FlushQueue)
                    except StopIteration:
                        pass
                return

            worker = selector(msg.node)
            if worker:
                job_sink[worker].send(msg)
            else:
                default_sink.send(run_job(*msg))

    for key, worker in workers.items():
        t = threading.Thread(
            target=patch,
            args=(worker.source, result_queue.sink))
        t.daemon = True
        t.start()

    return Connection(result_queue.source, dispatch_job)


def run_hybrid(wf, selector, workers):
    """
    Returns the result of evaluating the workflow; runs through several
    supplied workers in as many threads.

    :param wf:
        Workflow to compute
    :type wf: :py:class:`Workflow` or :py:class:`PromisedObject`

    :param selector:
        A function selecting the worker that should be run, given a hint.
    :param workers:
        A dictionary of workers

    :returns:
        result of running the workflow
    """
    worker = hybrid_threaded_worker(selector, workers)
    return Scheduler().run(worker, get_workflow(wf))
