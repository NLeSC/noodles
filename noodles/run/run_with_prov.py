from .connection import (Connection)
from .queue import (Queue)
from .scheduler import (Scheduler)
from .messages import (ResultMessage)
from .haploid import (
    pull, push, push_map, sink_map,
    branch, patch, broadcast)
from .thread_pool import (thread_pool)
from .worker import (worker, run_job)
from .job_keeper import (JobKeeper)

from ..workflow import (get_workflow, is_workflow)
from ..prov import (JobDB, prov_key)

from itertools import (repeat)
import threading


def run_single(wf, registry, jobdb_file, display=None):
    """Run a workflow in a single thread. This is the absolute minimal
    runner, consisting of a single queue for jobs and a worker running
    jobs every time a result is pulled.

    This version integrates with the JobDB.
    """
    registry = registry()
    db = JobDB(jobdb_file)

    def decode_result(key, obj):
        return ResultMessage(key, 'retrieved', registry.deep_decode(obj), None)

    @pull
    def pass_job(source):
        for key, job in source():
            job_msg = registry.deep_encode(job)
            prov = prov_key(job_msg)

            if db.job_exists(prov):
                status, _, result = db.get_result_or_attach(
                    key, prov, {})
                if status == 'retrieved':
                    yield decode_result(key, result)
                    continue
                elif status == 'attached':
                    continue

            db.new_job(key, prov, job_msg)
            result = run_job(key, job)
            result_msg = registry.deep_encode(result.value)
            db.store_result(key, result_msg)
            yield result

    S = Scheduler()
    W = Queue() >> pass_job

    return S.run(W, get_workflow(wf))


def start_job(db):
    """Adds a time stamp to the database."""
    @pull
    def start_job_f(source):
        for key, job in source():
            db.add_time_stamp(key, 'start')
            yield key, job

    return start_job_f


@sink_map
def print_result(key, status, result, msg):
    print(status, result)


def schedule_job(results, registry, db,
                 job_keeper=None, pred=lambda job: True):
    """Schedule a job, providing there is no result for it in the database yet.

    First the database checks if there is a previous job that is identical to
    the current one. If this is the case, the result is 'retrieved'.

    If there is no result, but the job description is in the database, either
    the job is still running, or it was tried before but Noodles crashed.

    In the first case, the job is 'attached' to the already running job.
    In the second case, the record of the previous job is deleted and the new
    job is scheduled.
    """
    @push
    def schedule_f(job_sink_):
        job_sink = job_sink_()
        result_sink = results.sink()

        while True:
            key, job = yield

            if pred(job):
                job_msg = registry.deep_encode(job)
                prov = prov_key(job_msg)

                if db.job_exists(prov):
                    status, other_key, result = db.get_result_or_attach(
                        key, prov, job_keeper)
                    if status == 'retrieved':
                        result_sink.send(
                            (key, 'retrieved',
                             registry.deep_decode(result, deref=True), None))
                        continue
                    elif status == 'attached':
                        continue
                    elif status == 'broken':
                        db.new_job(key, prov, job_msg)
                        job_sink.send((key, job))

                else:
                    db.new_job(key, prov, job_msg)
                    job_sink.send((key, job))

            else:
                job_sink.send((key, job))

    return schedule_f


def store_result_deep(registry, db, job_keeper=None, pred=lambda job: True):
    """When the result is known, we can insert it in the database. This is
    only done if the result is not a workflow. If the result is a workflow,
    a 'link' is added in the database, identifying the workflow by the Python
    `id` of the workflow object. When this workflow is finished the final
    result is inserted in the database."""
    def store_result(key, result, msg):
        result_msg = registry.deep_encode(result)
        attached = db.store_result(key, result_msg)
        if attached:
            for akey in attached:
                yield ResultMessage(akey, 'attached', result, msg)

    @pull
    def f(source):
        for key, status, result, msg in source():
            wf, n = job_keeper[key]
            job = wf.nodes[n]

            if pred(job):
                if is_workflow(result):
                    db.add_link(key, id(get_workflow(result)))
                else:
                    yield from store_result(key, result, msg)

            if wf.root == n:
                linked_jobs = db.get_linked_jobs(id(wf))

                if is_workflow(result):
                    for k in linked_jobs:
                        db.add_link(k, id(get_workflow(result)))

                else:
                    for k in linked_jobs:
                        yield from store_result(k, result, msg)

            yield ResultMessage(key, status, result, msg)

    return f


def run_parallel(wf, n_threads, registry, jobdb_file, job_keeper=None):
    """Run a workflow in `n_threads` parallel threads. Now we replaced the
    single worker with a thread-pool of workers.

    This version works with the JobDB to cache results."""
    registry = registry()
    db = JobDB(jobdb_file)

    if job_keeper is None:
        job_keeper = JobKeeper()
    S = Scheduler(job_keeper=job_keeper)

    jobs = Queue()
    results = Queue()

    assert job_keeper is not None

    LogQ = Queue()
    threading.Thread(
        target=patch,
        args=(LogQ.source, job_keeper.message),
        daemon=True).start()

    @push_map
    def log_job_start(key, job):
        return (key, 'start', job, None)

    r_src = jobs.source \
        >> start_job(db) \
        >> branch(log_job_start >> LogQ.sink) \
        >> thread_pool(*repeat(worker, n_threads), results=results) \
        >> store_result_deep(registry, db, job_keeper) \
        >> branch(LogQ.sink)

    j_snk = schedule_job(results, registry, db, job_keeper) >> jobs.sink

    return S.run(Connection(r_src, j_snk), get_workflow(wf))


def create_prov_worker(
        worker, results, registry, jobdb_file, job_keeper,
        pred=lambda x: True, log_q=None):
    registry = registry()
    db = JobDB(jobdb_file)

    jobs = Queue()

    r_src = jobs.source \
        >> start_job(db) \
        >> worker \
        >> store_result_deep(registry, db, job_keeper, pred)

    @push_map
    def log_job_sched(key, job):
        return (key, 'schedule', job, None)

    j_snk = broadcast(
        log_job_sched >> log_q.sink,
        schedule_job(results, registry, db, job_keeper, pred) >> jobs.sink)

    return Connection(r_src, j_snk)


def prov_wrap_connection(
        worker, results, registry, jobdb_file, job_keeper,
        pred=lambda x: True, log_q=None):
    registry = registry()
    db = JobDB(jobdb_file)

    r_src = worker.source \
        >> store_result_deep(registry, db, job_keeper, pred)

    @push_map
    def log_job_sched(key, job):
        return (key, 'schedule', job, None)

    j_snk = broadcast(
        log_job_sched >> log_q.sink,
        schedule_job(results, registry, db, job_keeper, pred) >> worker.sink)

    return Connection(r_src, j_snk)


def run_parallel_opt(wf, n_threads, registry, jobdb_file,
                     job_keeper=None, display=None, cache_all=False):
    """Run a workflow in `n_threads` parallel threads. Now we replaced the
    single worker with a thread-pool of workers.

    This version works with the JobDB to cache results; however we only store
    the jobs that are hinted with the 'store' keyword.

    :param wf:
        The workflow.

    :param n_threads:
        The number of threads to start.

    :param registry:
        The serialisation to use in order to store results in the database,
        as well as identify jobs.

    :param jobdb_file:
        The filename of the job database.

    :param job_keeper:
        The JobKeeper instance to keep runtime information in. If not given,
        we create one for you and throw it in the trash when we're done.

    :param display:
        The display routine to display activity. If not given, we won't report
        on any activity.
    """
    if job_keeper is None:
        job_keeper = JobKeeper()
    S = Scheduler(job_keeper=job_keeper)

    results = Queue()

    if cache_all:
        def pred(job):
            return True
    else:
        def pred(job):
            return job.hints and 'store' in job.hints

    LogQ = Queue()
    if display:
        tgt = broadcast(job_keeper.message, sink_map(display))
    else:
        tgt = job_keeper.message

    threading.Thread(
        target=patch,
        args=(LogQ.source, tgt),
        daemon=True).start()

    parallel_worker = \
        thread_pool(*repeat(worker, n_threads), results=results) >> \
        branch(LogQ.sink)

    return S.run(
        create_prov_worker(
            parallel_worker, results, registry, jobdb_file, job_keeper,
            pred, LogQ),
        get_workflow(wf))
