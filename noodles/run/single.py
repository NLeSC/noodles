from ..lib import (Queue)
from .worker import (worker)
from .scheduler import (Scheduler)
from ..workflow import (get_workflow)


def run_single(promise):
    """Evaluates a promise in single threaded mode."""
    Scheduler().run(
        Queue() >> worker,
        get_workflow(promise))
