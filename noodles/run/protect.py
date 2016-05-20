from functools import wraps

class CatchExceptions(object):
    """Catches exceptions running a function and passes them
    on to a Queue. This should be used when running a critical
    thread."""
    def __init__(self, sink):
        self.sink = sink
        self.jobs = set()

    def job_pass(self, key, job):
        self.jobs.add(key)

    def result_pass(self, key, status, result, err):
        self.jobs.remove(key)

    def __call__(self, fn):
        @wraps(fn)
        def protected_fn(*args, **kwargs):
            sink = self.sink()
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                for key in self.jobs:
                    sink.send((key, 'aborted', None, exc))

        return fn
