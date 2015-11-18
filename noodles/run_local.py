from .run_common import *
import threading

def single_worker():
    results = IOQueue()

    def do_job():
        sink = results.sink()
        sink.send(None)

        while True:
            key, job = yield
            sink.send((key, run_job(job)))

    return Connection(results.source, do_job)

def threaded_worker(n_threads):
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
