from .coroutines import (Connection, IOQueue, QueueConnection)
import threading


class Broker(object):
    def __init__(self, master=None):
        self.master = master
        self.slave = None

    def __gt__(self, other):
        if isinstance(other, tuple):
            return self > ThreadPool(*other)
        else:
            other.master = self.slave
            return Chain(self.master, end=other)

    def setup(self):
        return self.master.setup()


class Chain(Broker):
    def __init__(self, master, end):
        super(Chain, self).__init__(master=master)
        self.end = end

    @property
    def slave(self):
        return self.end.slave


class LocalWorker:
    def __init__(self):
        self.master = None

    def __call__(self):
        source, sink = self.master()

        def get_result():
            for key, job in source:
                yield (key, 'done', run_job(job), None)


class ThreadPool(Broker):
    def __init__(self, *stealers):
        self.stealers = stealers

        job_q = IOQueue()
        result_q = IOQueue()

        self.slave=QueueConnection(job_q, result_q)

        super(ThreadPool, self).__init__(
            master=QueueConnection(result_q, job_q))

        for s in self.stealers:
            t = threading.Thread(target=(self > s))
            t.deamon = True
            t.start()

    def __or__(self, other):
        other.master = self.slave
        def f():
            return patch()
