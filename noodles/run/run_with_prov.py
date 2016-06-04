from .connection import (Connection)
from .queue import (Queue)
from .scheduler import (Scheduler)
from .haploid import (send_map, sink_map, branch, patch)
from .thread_pool import (thread_pool)
from .worker import (worker)
from .job_keeper import (JobKeeper, JobTimer)

from ..workflow import (get_workflow)
from ..prov import (JobDB)

from itertools import (repeat)
import threading


def run_single(wf, registry, jobdb_file):
    """Run a workflow in a single thread. This is the absolute minimal 
    runner, consisting of a single queue for jobs and a worker running
    jobs every time a result is pulled."""
    registry = registry()
    db = JobDB(jobdb_file)

    @pull_map
    def encode_job(key, job):
        return key, registry.deep_encode(job.node)

    def decode_result(key, obj):
        return key, 'stored', registry.deep_decode(obj), None

    S = Scheduler()
    W = Queue() \
        .to(first_of(encode.to(db.new_job).to(db.get_result).maybe_to(decode_result),
                     worker.to(branch(db_store_result))))

    return S.run(W, get_workflow(wf))


def run_parallel(wf, n_threads, registry, jobdb_file):
    """Run a workflow in `n_threads` parallel threads. Now we replaced the single
    worker with a thread-pool of workers."""
    S = Scheduler()
    W = Queue() \
        .to(thread_pool(*repeat(worker, n_threads)))

    return S.run(W, get_workflow(wf))


