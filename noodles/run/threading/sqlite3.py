from ..scheduler import (Scheduler)
from ..messages import (ResultMessage)
from ..worker import (worker)
from ..logging import make_logger

from ...workflow import (get_workflow)
from ...prov.sqlite import (JobDB)
from ...lib import (
    Queue, pull, thread_pool, Connection, EndOfQueue,
    pull_map, push_map)

from itertools import repeat


def run_parallel(workflow, *, n_threads, registry, db_file):
    """Run a workflow in parallel threads, storing results in a Sqlite3
    database.

    :param workflow: Workflow or PromisedObject to evaluate.
    :param n_threads: number of threads to use (in addition to the scheduler).
    :param registry: serialization Registry function.
    :param db_file: filename of Sqlite3 database, give `':memory:'` to
        keep the database in memory only.
    :return: Evaluated result.
    """
    with JobDB(db_file, registry) as db:
        job_queue = Queue()
        result_queue = Queue()

        @pull
        def pass_job(job_source):
            result_sink = result_queue.sink()

            for message in job_source():
                if message is EndOfQueue:
                    return

                key, job = message

                status, retrieved_result = db.add_job_to_db(key, job)

                if status == 'retrieved':
                    result_sink.send(retrieved_result)
                    continue

                elif status == 'attached':
                    continue

                else:
                    yield message

        job_logger = make_logger("worker", push_map, db)

        @pull
        def pass_result(worker_source):
            for result in worker_source():
                if result is EndOfQueue:
                    return

                attached = db.store_result_in_db(result)

                yield result
                yield from (ResultMessage(key, 'attached', result.value, None)
                            for key in attached)

        result_logger = make_logger("worker", pull_map, db)

        worker_pool = job_queue.source >> pass_job >> thread_pool(
            *repeat(worker, n_threads), results=result_queue)
        job_front_end = job_logger >> job_queue.sink
        result_front_end = worker_pool >> pass_result >> result_logger

        scheduler = Scheduler(job_keeper=db)
        parallel_sqlite_worker = Connection(result_front_end, job_front_end)

        return scheduler.run(parallel_sqlite_worker, get_workflow(workflow))
