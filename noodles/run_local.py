from .run_common import *
import threading
import time

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
            yield (key, run_job(job))

    return Connection(get_result, jobs.sink)

def threaded_worker(n_threads):
    """
    Sets up a number of threads, each polling for jobs.

    :returns:
        Connection to the job and result queues
    :rtype: :py:class:`Connection`
    """
    job_q    = IOQueue()
    result_q = IOQueue()

    worker_connection    = QueueConnection(job_q, result_q)
    scheduler_connection = QueueConnection(result_q, job_q)

    def worker(source, sink):
        for key, job in source:
            sink.send((key, run_job(job)))

    for i in range(n_threads):
        t = threading.Thread(
            target = worker,
            args   = worker_connection.setup())

        t.daemon = True
        t.start()

    return scheduler_connection

def run(wf):
    worker = single_worker()
    return Scheduler().run(worker, get_workflow(wf))

def run_parallel(wf, n_threads):
    worker = threaded_worker(n_threads)
    return Scheduler().run(worker, get_workflow(wf))
