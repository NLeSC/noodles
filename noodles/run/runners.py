from .connection import (Connection)
from .queue import (Queue)
from .scheduler import (Scheduler)
from .haploid import (send_map, sink_map, branch, patch)
from .thread_pool import (thread_pool)
from .worker import (worker)
from ..workflow import (get_workflow)
from .job_keeper import (JobKeeper, JobTimer)

from itertools import (repeat)
import threading


def run_single(wf):
    """Run a workflow in a single thread. This is the absolute minimal 
    runner, consisting of a single queue for jobs and a worker running
    jobs every time a result is pulled."""
    S = Scheduler()
    W = Queue() \
        .to(worker)

    return S.run(W, get_workflow(wf))


def run_parallel(wf, n_threads):
    """Run a workflow in `n_threads` parallel threads. Now we replaced the single
    worker with a thread-pool of workers."""
    S = Scheduler()
    W = Queue() \
        .to(thread_pool(*repeat(worker, n_threads)))

    return S.run(W, get_workflow(wf))


@send_map
def log_job_start(key, job):
    return (key, 'start', job, None)


@send_map
def log_job_schedule(key, job):
    return (key, 'schedule', job, None)

def run_parallel_timing(wf, n, timing_file):
    LogQ = Queue()

    J = JobTimer(timing_file)
    S = Scheduler(job_keeper=J)
    t = threading.Thread(
        target=patch,
        args=(LogQ.source, J.message),
        daemon=True).start()

    W = Queue() \
        .to(branch(log_job_start.to(LogQ.sink))) \
        .to(thread_pool(*repeat(worker, n))) \
        .to(branch(LogQ.sink))

    result = S.run(W, get_workflow(wf))
    LogQ.wait()
    return result

def run_single_with_display(wf, display):
    """Adds a display to the single runner. Everything still runs in a single
    thread. Every time a job is pulled by the worker, a message goes to the display
    routine; when the job is finished the result is sent to the display routine."""
    S = Scheduler()
    W = Queue() \
        .to(branch(log_job_start.to(sink_map(display)))) \
        .to(worker) \
        .to(branch(sink_map(display)))

    return S.run(W, get_workflow(wf))


def run_parallel_with_display(wf, n, display):
    """Adds a display to the parallel runner. Because messages come in asynchronously
    now, we start an extra thread just for the display routine."""
    LogQ = Queue()

    S = Scheduler()
    
    t = threading.Thread(
        target=patch, 
        args=(LogQ.source, sink_map(display)), 
        daemon=True).start()

    W = Queue() \
        .to(branch(log_job_start.to(LogQ.sink))) \
        .to(thread_pool(*repeat(worker, n))) \
        .to(branch(LogQ.sink))

    result = S.run(W, get_workflow(wf))
    LogQ.wait()
    del t

    return result

