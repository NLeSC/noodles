import threading

from ..workflow import get_workflow
from .coroutines import IOQueue, Connection, QueueConnection
from .scheduler import run_job, Scheduler


def single_worker():
    """
    Sets up a single worker co-routine.

    :returns:
        Connection to the worker.
    :rtype: :py:class:`Connection`
    """
    jobs = IOQueue()

    def get_result():
        source = jobs.source()

        for key, job in source:
            yield (key, 'done', run_job(job), None)

    return Connection(get_result, jobs.sink)


def threaded_worker(n_threads):
    """
    Sets up a number of threads, each polling for jobs.

    :param n_threads:
        Number of threads to spawn.
    :type n_threads: int

    :returns:
        Connection to the job and result queues
    :rtype: :py:class:`Connection`
    """
    job_q = IOQueue()
    result_q = IOQueue()

    worker_connection = QueueConnection(job_q, result_q)
    scheduler_connection = QueueConnection(result_q, job_q)

    def worker(source, sink):
        for key, job in source:
            sink.send((key, 'done', run_job(job), None))

    for i in range(n_threads):
        t = threading.Thread(
            target=worker,
            args=worker_connection.setup())

        t.daemon = True
        t.start()

    return scheduler_connection


def run_single(wf, verbose=False):
    """
    Returns the result of evaluting the workflow

    :param wf:
        Workflow to compute
    :type wf: :py:class:`Workflow` or :py:class:`PromisedObject`
    """
    worker = single_worker()
    return Scheduler(verbose).run(worker, get_workflow(wf))


def run_parallel(wf, n_threads):
    """
    Returns the result of evaluating the workflow; runs in several threads.

    :param wf:
        Workflow to compute
    :type wf: :py:class:`Workflow` or :py:class:`PromisedObject`

    :param n_threads:
        Number of threads to use
    :type n_threads: int
    """
    worker = threaded_worker(n_threads)
    return Scheduler().run(worker, get_workflow(wf))
