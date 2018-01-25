from .scheduler import (Scheduler)
from .messages import (ResultMessage)
from .worker import (run_job)

from ..workflow import (get_workflow)
from ..prov.sqlite import (JobDB)
from ..lib import (Queue, pull)


def run_single(wf, registry, db_file):
    """Run a workflow in a single thread. This is the absolute minimal
    runner, consisting of a single queue for jobs and a worker running
    jobs every time a result is pulled.

    This version integrates with the JobDB.
    """
    db = JobDB(db_file, registry)

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
    single_worker = Queue() >> pass_job

    return scheduler.run(single_worker, get_workflow(wf))
