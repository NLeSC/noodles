from functools import wraps
from .messages import (ResultMessage)
from .haploid import (push_map, pull_map)
import threading


def source_branch(*flst):
    @pull_map
    def g(*args):
        for f in flst:
            f(*args)
        return args

    return g


def sink_branch(*flst):
    @push_map
    def g(*args):
        for f in flst:
            f(*args)
        return args

    return g


class CatchExceptions(object):
    """Catches exceptions running a function and passes them
    on to a Queue. This should be used when running a critical
    thread.

    The CatchExceptions object has two important members:
    `job_pass` and `result_pass`, the first is a `pull_map`,
    the second a `send_map`, assuming we pull and send to an
    intermediate queue."""
    def __init__(self, sink):
        self.sink = sink
        self.jobs = set()
        self.lock = threading.Lock()

        self.job_sink = sink_branch(self.job_pass)
        self.job_source = source_branch(self.job_pass)
        self.result_sink = sink_branch(self.result_pass)
        self.result_source = source_branch(self.result_pass)

    def job_pass(self, key, job):
        with self.lock:
            self.jobs.add(key)

    def result_pass(self, key, status, result, err):
        with self.lock:
            self.jobs.remove(key)

    def __call__(self, fn):
        @wraps(fn)
        def protected_fn(*args, **kwargs):
            sink = self.sink()
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                with self.lock:
                    for key in self.jobs:
                        sink.send(ResultMessage(key, 'aborted', None, exc))

                raise exc

        return protected_fn
