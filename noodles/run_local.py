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

def map_dict(f, d):
    return dict((k, f(v)) for k, v in d.items())

def unzip_dict(d):
    a = {}
    b = {}

    for k, (v, w) in d.items():
        a[k] = v
        b[k] = w

    return a, b

def threaded_worker(n_threads, blocking_results_q = True):
    """
    Sets up a number of threads, each polling for jobs.

    :returns:
        Connection to the job and result queues
    :rtype: :py:class:`Connection`
    """
    job_q    = IOQueue(True)
    result_q = IOQueue(blocking_results_q)

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

def hybrid_worker(selector, workers, fall_back = threaded_worker(1)):
    """
    :param selector:
        The selector function takes a hint that was attached to a job
        and returns the prefered worker (by key into the workers dict).
    :param workers:
        A dictionary of workers.
    :param fall_back:
        The worker to use if no hints were given.
    """
    sources, sinks     = unzip_dict(map_dict(lambda w: w.setup(), workers))
    fb_source, fb_sink = fall_back.setup()
    sources['__default__'] = fb_source

    @coroutine_sink
    def dispatch_job():
        while True:
            key, job = yield
            h = get_hints(job)
            print("dispatching: ", job.foo.__name__, job.hints)
            sinks.get(selector(h), fb_sink).send((key, job))

    return Connection(merge_sources(*sources.values()), dispatch_job)

def run(wf):
    worker = single_worker()
    return Scheduler().run(worker, get_workflow(wf))

def run_parallel(wf, n_threads):
    worker = threaded_worker(n_threads)
    return Scheduler().run(worker, get_workflow(wf))
