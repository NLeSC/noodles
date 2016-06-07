from .connection import (Connection)
from .queue import (Queue)
from .scheduler import (Scheduler)
from .haploid import (pull, push, push_map, pull_map, sink_map, branch, patch, composer)
from .thread_pool import (thread_pool)
from .worker import (worker, run_job)
from .job_keeper import (JobKeeper, JobTimer)

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

    @pull_map
    def pass_job(key, job):
        job_msg = registry.deep_encode(job)
        prov = prov_key(job_msg)

        result = db.get_result(prov)
        if result:
            return decode_result(key, result)
        
        db.new_job(key, prov, job_msg)
        result = run_job(key, job)
        result_msg = registry.deep_encode(result.value)
        db.store_result(key, result_msg)

        return result
    
    S = Scheduler()
    W = Queue() >> pass_job

    return S.run(W, get_workflow(wf))


def run_parallel(wf, n_threads, registry, jobdb_file):
    """Run a workflow in `n_threads` parallel threads. Now we replaced the single
    worker with a thread-pool of workers."""
    registry = registry()
    db = JobDB(jobdb_file)

    S = Scheduler()

    jobs = Queue()
    results = Queue()

    def decode_result(key, obj):
        return key, 'retrieved', registry.deep_decode(obj), None

    @push
    def schedule_job():
        job_sink = jobs.sink()
        result_sink = results.sink()

        while True:
            key, job = yield
            job_msg = registry.deep_encode(job)
            prov = prov_key(job_msg)

            result = db.get_result(prov)
            if result:
                result_sink.send(decode_result(key, result))
                continue
        
            db.new_job(key, prov, job_msg)
            job_sink.send((key, job))
    
    @pull
    def start_job(source):
        for key, job in source():
            db.add_time_stamp(key, 'start')
            yield key, job

    @pull
    def store_result(source):
        for result in source():    
            result_msg = registry.deep_encode(result.value)
            db.store_result(result.key, result_msg)
            yield result
    
    @pull
    def print_result(source):
        for result in source():
            print(result)
            yield result
             
    r = jobs >> start_job >> thread_pool(*repeat(worker, n_threads), results=results)
    j_snk = schedule_job
    
    return S.run(Connection(r.source, j_snk), get_workflow(wf))


