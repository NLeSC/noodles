from .run_common import *
from .utility import map_dict, unzip_dict

import threading

def hybrid_coroutine_worker(selector, workers):
    jobs = IOQueue()

    worker_source, worker_sink = unzip_dict(
        map_dict(lambda w: w.setup(), workers))

    def get_result():
        source = jobs.source()

        for key, job in source:
            if job.hints == None:
                yield (key, run_job(job))
            else:
                worker = selector(job.hints)
                # send the worker a job and wait for it to return
                worker_sink[worker].send((key, job))
                result = next(worker_source[worker])
                yield result

    return Connection(get_result, jobs.sink)

def hybrid_threaded_worker(selector, workers):
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

    def result_proxy(source):
        sink = results.sink()

        for result in source:
            sink.send(result)

    for k, v in worker_source.items():
        t = threading.Thread(
            target = result_proxy,
            args = (v,))
        t.daemon = True
        t.start()

    return Connection(results.source, dispatch_job)
