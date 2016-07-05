from .haploid import (pull_map)
from .scheduler import (Result)
from ..interface import (AnnotatedValue, JobException)
from ..utility import (object_name)
import sys


@pull_map
def worker(key, job):
    return run_job(key, job)


def run_job(key, job):
    """A worker coroutine. Pulls jobs, yielding results. If an
    exception is raised running the job, it returns a result
    object with 'error' status. If the job requests return-value
    annotation, a two-tuple is expected; this tuple is then
    unpacked, the first being the result, the second part is
    sent on in the error message slot."""
    try:
        if job.hints and 'annotated' in job.hints:
            result = job.apply()
            if isinstance(result, tuple) and len(result) == 2:
                value, msg = result
                return Result(key, 'done', value, msg)
            else:
                raise TypeError("You promised annotation in call "
                                "to function {} but return value "
                                "is incompatible with 2-tuple."
                                .format(object_name(job.foo)))

        else:
            result = job.apply()
            if isinstance(result, AnnotatedValue):
                value, message = result
                return Result(key, 'done', value, message)

            return Result(key, 'done', result, None)

    except Exception as error:
        exc_info = sys.exc_info()
        return Result(key, 'error', None, JobException(*exc_info))
