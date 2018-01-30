from ..scheduler import (Scheduler)
from ..messages import (ResultMessage)
from ..worker import (run_job)
from ..logging import make_logger

from ...workflow import (get_workflow)
from ...prov.sqlite import (JobDB)
from ...lib import (Queue, pull, pull_map, push_map, Connection)


def run_single(workflow, *, registry, db_file):
    """"Run workflow in a single thread, storing results in a Sqlite3
    database.

    :param workflow: Workflow or PromisedObject to be evaluated.
    :param registry: serialization Registry function.
    :param db_file: filename of Sqlite3 database, give `':memory:'` to
        keep the database in memory only.
    :return: Evaluated result.
    """
    with JobDB(db_file, registry) as db:
        job_logger = make_logger("worker", push_map, db)
        result_logger = make_logger("worker", pull_map, db)

        @pull
        def pass_job(source):
            for msg in source():
                key, job = msg
                status, retrieved_result = db.add_job_to_db(key, job)

                if status == 'retrieved':
                    yield retrieved_result
                    continue

                elif status == 'attached':
                    continue

                result = run_job(key, job)
                attached = db.store_result_in_db(result)

                yield result
                yield from (ResultMessage(key, 'attached', result.value, None)
                            for key in attached)

        scheduler = Scheduler(job_keeper=db)
        queue = Queue()
        job_front_end = job_logger >> queue.sink
        result_front_end = queue.source >> pass_job >> result_logger
        single_worker = Connection(result_front_end, job_front_end)

        return scheduler.run(single_worker, get_workflow(workflow))
