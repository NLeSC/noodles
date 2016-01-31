from .coroutines import (IOQueue, QueueConnection, coroutine_sink)
from .scheduler import (run_job, Scheduler)
from ..datamodel import (get_workflow)
import threading
import subprocess


@coroutine_sink
def splice_sink(a, b):
    while True:
        value = yield
        b.send(value)
        a.send(value)


def siphon_source(source, sink):
    for value in source:
        sink.send(value)
        yield value


class Logger:
    def __init__(self):
        self.msg_q = IOQueue()
        self.jobs = {}

    @coroutine_sink
    def job_sink(self):
        msg_sink = self.msg_q.sink()
        while True:
            key, job = yield
            msg_sink.send(('start', key))

    @coroutine_sink
    def result_sink(self):
        msg_sink = self.msg_q.sink()
        while True:
            key, result = yield
            msg_sink.send(('finish', key))

    def run(self):
        source = self.msg_q.source()
        for key, args in source:
            print(key, args)


def logging_worker(n_threads):
    """Sets up a number of threads, each polling for jobs.

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

    log = Logger()

    def worker(source, sink):
        splice = splice_sink(sink, log.result_sink())
        for key, job in siphon_source(source, log.job_sink()):
            try:
                result = run_job(job)
                splice.send((key, result))

            except subprocess.CalledProcessError as err_msg:
                print(err_msg.stderr)
                splice.send((key, 'ERROR!'))

    for i in range(n_threads):
        t = threading.Thread(
            target=worker,
            args=worker_connection.setup())

        t.daemon = True
        t.start()

    t_log = threading.Thread(target=log.run)
    t_log.daemon = True
    t_log.start()

    return scheduler_connection


def run_logging(wf, n_threads):
    """
    Returns the result of evaluating the workflow; runs in several threads.

    :param wf:
        Workflow to compute
    :type wf: :py:class:`Workflow` or :py:class:`PromisedObject`

    :param n_threads:
        Number of threads to use
    :type n_threads: int
    """
    worker = logging_worker(n_threads)
    return Scheduler().run(worker, get_workflow(wf))
