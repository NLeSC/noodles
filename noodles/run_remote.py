from .run_common import *

def single_worker():
    result = None

    def do_job():
        nonlocal result
        while True:
            key, job = yield
            result = key, run_job(job)

    def send_result():
        nonlocal result
        while True:
            yield result

    results = send_result()
    worker  = do_job()
    do_job.send(None)

    return results, worker

def threaded_worker(n_threads):
    job_queue = IOQueue()
    result_queue = IOQueue()

    worker_connection    = Connection(job_q, result_q)
    scheduler_connection = Connection(result_q, job_q)

    source, sink = worker_connection.setup()

    def worker(source, sink):
        for key, job in source:
            sink.send((key, run_job(job)))

    for i in range(n_threads):
        t = threading.Thread(
            target = worker,
            args   = connection.setup())

        t.daemon = True
        t.start()

    return scheduler_connection
