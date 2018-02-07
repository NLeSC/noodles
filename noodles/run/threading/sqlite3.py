"""
Implements parallel worker with Sqlite database.
"""

from itertools import repeat
import logging

from ..scheduler import (Scheduler)
from ..messages import (ResultMessage)
from ..worker import (worker)
from ..logging import make_logger

from ...workflow import (get_workflow)
from ...prov.sqlite import (JobDB)
from ...lib import (
    Queue, pull, thread_pool, Connection, EndOfQueue,
    pull_map, push_map)


def pass_job(db: JobDB, result_queue: Queue, always_cache=False):
    """Create a pull stream that receives jobs and passes them on to the
    database. If the job already has a result, that result is pushed onto
    the `result_queue`.
    """
    @pull
    def pass_job_stream(job_source):
        """Pull stream instance created by `pass_job`."""
        result_sink = result_queue.sink()

        for message in job_source():
            if message is EndOfQueue:
                return

            key, job = message
            if always_cache or ('store' in job.hints):
                status, retrieved_result = db.add_job_to_db(key, job)

                if status == 'retrieved':
                    result_sink.send(retrieved_result)
                    continue

                elif status == 'attached':
                    continue

            yield message

    return pass_job_stream


def pass_result(db: JobDB, always_cache=False):
    """Creates a pull stream receiving results, storing them in the database,
    then sending them on. At this stage, the database may return a list of
    attached jobs which also need to be sent on to the scheduler."""
    @pull
    def pass_result_stream(worker_source):
        """Pull stream instance created by `pass_result`."""
        for result in worker_source():
            if result is EndOfQueue:
                return

            attached = db.store_result_in_db(
                result, always_cache=always_cache)

            yield result
            yield from (ResultMessage(key, 'attached', result.value, None)
                        for key in attached)

    return pass_result_stream


def run_parallel(
        workflow, *, n_threads, registry, db_file, echo_log=True,
        always_cache=False):
    """Run a workflow in parallel threads, storing results in a Sqlite3
    database.

    :param workflow: Workflow or PromisedObject to evaluate.
    :param n_threads: number of threads to use (in addition to the scheduler).
    :param registry: serialization Registry function.
    :param db_file: filename of Sqlite3 database, give `':memory:'` to
        keep the database in memory only.
    :param echo_log: set log-level high enough
    :param always_cache: enable caching by schedule hint.
    :return: Evaluated result.
    """
    if echo_log:
        logging.getLogger('noodles').setLevel(logging.DEBUG)
        logging.debug("--- start log ---")

    with JobDB(db_file, registry) as db:
        job_queue = Queue()
        result_queue = Queue()

        job_logger = make_logger("worker", push_map, db)
        result_logger = make_logger("worker", pull_map, db)

        worker_pool = job_queue.source \
            >> pass_job(db, result_queue, always_cache) \
            >> thread_pool(*repeat(worker, n_threads), results=result_queue)
        job_front_end = job_logger >> job_queue.sink
        result_front_end = worker_pool \
            >> pass_result(db, always_cache) \
            >> result_logger

        scheduler = Scheduler(job_keeper=db)
        parallel_sqlite_worker = Connection(result_front_end, job_front_end)

        result = scheduler.run(parallel_sqlite_worker, get_workflow(workflow))

    return registry().dereference(result)
