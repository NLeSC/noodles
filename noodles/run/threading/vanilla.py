from ..worker import worker
from ..scheduler import Scheduler
from ...lib import (Queue, thread_pool)
from ...workflow import get_workflow

from itertools import repeat


def run_parallel(workflow, n_threads):
    """Run a workflow in parallel threads.

    :param workflow: Workflow or PromisedObject to evaluate.
    :param n_threads: number of threads to use (in addition to the scheduler).
    :returns: evaluated workflow.
    """
    scheduler = Scheduler()
    threaded_worker = Queue() >> thread_pool(
        *repeat(worker, n_threads))

    return scheduler.run(threaded_worker, get_workflow(workflow))
