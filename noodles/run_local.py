from .run_common import *
import threading

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

def hybrid_worker(selector, workers, fall_back = single_worker()):
    """
    :param selector:
        The selector function takes a hint that was attached to a job
        and returns the prefered worker (by key into the workers dict).
    :param workers:
        A dictionary of workers.
    :param fall_back:
        The worker to use if no hints were given.
    """

    connections = dict((key, w.setup()) for w in workers)
    fbc = fall_back.setup()

    def do_job():
        while True:
            key, job = yield
            h = get_hints(job)
            w = fbc if not h else connections[selector(h)]





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
    """
    Returns the result of evaluting the workflow

    :param workflow:
        Workflow to compute
    :type workflow: :py:class:`Workflow` or :py:class:`PromisedObject`
    """
    worker = single_worker()
    return Scheduler().run(worker, get_workflow(wf))

def run_parallel(wf, n_threads):
    """
    Returns the result of evaluating the workflow; runs in several threads.

    :param workflow:
        Workflow to compute
    :type workflow: :py:class:`Workflow` or :py:class:`PromisedObject`

    :param n_threads:
        Number of threads to use
    :type n_threads: int
    """
    worker = threaded_worker(n_threads)
    return Scheduler().run(worker, get_workflow(wf))
