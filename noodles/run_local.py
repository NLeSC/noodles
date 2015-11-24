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

def map_dict(f, d):
    return dict((k, f(v)) for k, v in d.items())

def unzip_dict(d):
    a = {}
    b = {}

    for k, (v, w) in d.items():
        a[k] = v
        b[k] = w

    return a, b

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

def hybrid_worker(selector, workers, fall_back):
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

    result_q = IOQueue()
    sink = result_q.sink()

    def gather_results():
        while True:
            got_result = False
            for k, s in sources.items():
                v = next(s)
                print("polling {0}:".format(k), v)
                if v:
                    got_result = True
                    sink.send(v)

            if not got_result:
                time.sleep(0.1)

    t = threading.Thread(target = gather_results)
    t.daemon = True
    t.start()

    @coroutine_sink
    def dispatch_job():
        while True:
            key, job = yield
            h = get_hints(job)
            print("dispatching {0}: ".format(job.hints), job.foo.__name__, job.bound_args)
            sinks.get(selector(h), fb_sink).send((key, job))

    return Connection(result_q.source, dispatch_job)

def run(wf):
    worker = single_worker()
    return Scheduler().run(worker, get_workflow(wf))

def run_parallel(wf, n_threads):
    worker = threaded_worker(n_threads)
    return Scheduler().run(worker, get_workflow(wf))
