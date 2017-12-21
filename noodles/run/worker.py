from ..lib import (pull_map, EndOfQueue)
from .messages import (ResultMessage, JobMessage)
import sys


@pull_map
def worker(job):
    """Primary |worker| coroutine. This is a |pull| object that pulls jobs from
    a source and yield evaluated results.

    Input should be of type |JobMessage|, output of type |ResultMessage|.

    .. |worker| replace:: :py:func::`worker`"""
    if job is EndOfQueue:
        return

    if not isinstance(job, JobMessage):
        print("Warning: Job should be communicated using `JobMessage`.",
              file=sys.stderr)

    key, node = job
    return run_job(key, node)


def run_job(key, node):
    """Run a job. This applies the function node, and returns a |ResultMessage|
    when complete. If an exception is raised in the job, the |ResultMessage|
    will have ``'error'`` status.

    .. |run_job| replace:: :py:func:`run_job`"""
    try:
        result = node.apply()
        return ResultMessage(key, 'done', result, None)

    except Exception as exc:
        return ResultMessage(key, 'error', None, exc)
