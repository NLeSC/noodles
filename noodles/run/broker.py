from .coroutines import (Connection, IOQueue, QueueConnection, patch, coroutine)
import threading
from .haploid import (haploid, Haploid, send_map, branch)
from .thread_pool import (thread_pool)
from .queue import (Queue)



# The runners
from .scheduler import (Scheduler, Result)
from ..workflow import get_workflow
from .job_keeper import JobKeeper

from itertools import repeat, starmap
from functools import partial

#@haploid('pull')
#def worker(source):


def run_single(wf):
    J = JobKeeper()
    S = Scheduler(job_keeper=J)
    W = Queue() \
        .to(worker) \
        .to(branch(sink_map(J.store_result)))

    return S.run(W, get_workflow(wf))


def run_parallel(wf, n):
    J = JobKeeper()
    S = Scheduler(job_keeper=J)
    W = Queue() \
        .to(thread_pool(*repeat(worker, n))) \
        .to(branch(sink_map(J.store_result)))

    return S.run(W, get_workflow(wf))


@send_map
def log_job_start(key, job):
    return (key, 'start', job, None)


@send_map
def log_job_schedule(key, job):
    return (key, 'schedule', job, None)


def run_single_with_display(wf, display):
    S = Scheduler()
    W = Queue() \
        .to(branch(log_job_start.to(sink_map(display)))) \
        .to(worker) \
        .to(branch(sink_map(display)))

    return S.run(W, get_workflow(wf))


def run_parallel_with_display(wf, n, display):
    LogQ = Queue()

    S = Scheduler()
    
    t = threading.Thread(
        target=patchl, 
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

