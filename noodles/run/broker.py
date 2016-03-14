from .coroutines import (Connection, IOQueue, QueueConnection)
import threading


class Broker(object):
    def __init__(self, master, slave):
        self.master = master
        self.slave = slave

    def __or__(self, other):
        if isinstance(other, tuple):
            return self | ThreadPool(*other)



    def __lt__(self, others):
        pass


class LocalWorker()

class ThreadPool(Broker):
    def __init__(self, *stealers):
        self.stealers = stealers

        job_q = IOQueue()
        result_q = IOQueue()

        super(ThreadPool, self).__init__(
            slave=QueueConnection(job_q, result_q),
            master=QueueConnection(result_q, job_q))

    def __call__(self):
        for s in self.stealers:
            t = threading.Thread(target=(self | s))
            t.deamon = True
            t.start()

