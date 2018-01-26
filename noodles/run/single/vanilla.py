from ..worker import (worker)
from ..scheduler import (Scheduler)
from ...lib import (Queue)
from ...workflow import (get_workflow)


def run_single(workflow):
    """"Run workflow in a single thread (same as the scheduler).

    :param workflow: Workflow or PromisedObject to be evaluated.
    :return: Evaluated result.
    """
    return Scheduler().run(
        Queue() >> worker,
        get_workflow(workflow))
