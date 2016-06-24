from .connection import (Connection)
from .queue import (Queue)
from .scheduler import (Scheduler)
from .haploid import (pull, push, push_map, sink_map, branch, patch)
from .thread_pool import (thread_pool)
from .worker import (worker, run_job)
from .job_keeper import (JobKeeper)

from ..workflow import (get_workflow)
from ..prov import (JobDB, prov_key)

from itertools import (repeat)
import threading


def run_single(wf, registry, jobdb_file):
    """Run a workflow in a single thread. This is the absolute minimal
    runner, consisting of a single queue for jobs and a worker running
    jobs every time a result is pulled."""
    registry = registry()
    db = JobDB(jobdb_file)

    def decode_result(key, obj):
        return key, 'retrieved', registry.deep_decode(obj), None

    @pull
    def pass_job(source):
        for key, job in source():
            job_msg = registry.deep_encode(job)
            prov = prov_key(job_msg)

            if db.job_exists(prov):
                status, other_key, result = db.get_result_or_attach(
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


def run_parallel(wf, n_threads, registry, jobdb_file, job_keeper=None):
    """Run a workflow in `n_threads` parallel threads. Now we replaced the single
    worker with a thread-pool of workers."""
    registry = registry()
    db = JobDB(jobdb_file)

    if job_keeper is None:
        job_keeper = JobKeeper()
    S = Scheduler(job_keeper=job_keeper)

    jobs = Queue()
    results = Queue()

    @push
    def schedule_job():
        job_sink = jobs.sink()
        result_sink = results.sink()

        while True:
            key, job = yield
            job_msg = registry.deep_encode(job)
            prov = prov_key(job_msg)

            if db.job_exists(prov):
                status, other_key, result = db.get_result_or_attach(
                    key, prov, job_keeper)
                if status == 'retrieved':
                    result_sink.send((
                        key, 'retrieved', registry.deep_decode(result), None))
                    continue
                elif status == 'attached':
                    continue
                elif status == 'broken':
                    db.new_job(key, prov, job_msg)
                    job_sink.send((key, job))

            else:
                db.new_job(key, prov, job_msg)
                job_sink.send((key, job))

    @pull
    def start_job(source):
        for key, job in source():
            db.add_time_stamp(key, 'start')
            yield key, job

    @pull
    def store_result(source):
        for key, status, result, msg in source():
            result_msg = registry.deep_encode(result)
            attached = db.store_result(key, result_msg)

            yield (key, status, result, msg)
            if attached:
                for key in attached:
                    yield (key, 'attached', result, msg)

    @sink_map
    def print_result(key, status, result, msg):
        print(status, result)

    if job_keeper is not None:
        LogQ = Queue()
        threading.Thread(
            target=patch,
            args=(LogQ.source, job_keeper.message),
            daemon=True).start()

        @push_map
        def log_job_start(key, job):
            return (key, 'start', job, None)

        r_src = jobs.source \
            >> start_job \
            >> branch(log_job_start >> LogQ.sink) \
            >> thread_pool(*repeat(worker, n_threads), results=results) \
            >> store_result \
            >> branch(LogQ.sink)

        j_snk = schedule_job

        return S.run(Connection(r_src, j_snk), get_workflow(wf))

    else:
        r_src = jobs.source \
            >> start_job \
            >> thread_pool(*repeat(worker, n_threads), results=results) \
            >> store_result \
            >> branch(print_result)

        j_snk = schedule_job

        return S.run(Connection(r_src, j_snk), get_workflow(wf))


def run_parallel_opt(wf, n_threads, registry, jobdb_file, job_keeper=None):
    """Run a workflow in `n_threads` parallel threads. Now we replaced the single
    worker with a thread-pool of workers."""
    registry = registry()
    db = JobDB(jobdb_file)

    if job_keeper is None:
        job_keeper = JobKeeper()
    S = Scheduler(job_keeper=job_keeper)

    jobs = Queue()
    results = Queue()

    @push
    def schedule_job():
        job_sink = jobs.sink()
        result_sink = results.sink()

        while True:
            key, job = yield

            if job.hints and 'store' in job.hints:
                job_msg = registry.deep_encode(job)
                prov = prov_key(job_msg)

                if db.job_exists(prov):
                    status, other_key, result = db.get_result_or_attach(
                        key, prov, job_keeper)
                    if status == 'retrieved':
                        result_sink.send(
                            (key, 'retrieved',
                             registry.deep_decode(result), None))
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

    @pull
    def start_job(source):
        for key, job in source():
            db.add_time_stamp(key, 'start')
            yield key, job

    @pull
    def store_result(source):
        for key, status, result, msg in source():
            job = job_keeper[key].node

            if job.hints and 'store' in job.hints:
                result_msg = registry.deep_encode(result)
                attached = db.store_result(key, result_msg)

                if attached:
                    for akey in attached:
                        yield (akey, 'attached', result, msg)

            yield (key, status, result, msg)

    @sink_map
    def print_result(key, status, result, msg):
        print(status, result)

    if job_keeper is not None:
        LogQ = Queue()
        threading.Thread(
            target=patch,
            args=(LogQ.source, job_keeper.message),
            daemon=True).start()

        @push_map
        def log_job_start(key, job):
            return (key, 'start', job, None)

        r_src = jobs.source \
            >> start_job \
            >> branch(log_job_start >> LogQ.sink) \
            >> thread_pool(*repeat(worker, n_threads), results=results) \
            >> store_result \
            >> branch(LogQ.sink)

        j_snk = schedule_job

        return S.run(Connection(r_src, j_snk), get_workflow(wf))

    else:
        r_src = jobs.source \
            >> start_job \
            >> thread_pool(*repeat(worker, n_threads), results=results) \
            >> store_result \
            >> branch(print_result)

        j_snk = schedule_job

        return S.run(Connection(r_src, j_snk), get_workflow(wf))
