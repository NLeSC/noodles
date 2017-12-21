from ..lib import (Queue)
from .worker import (worker)
from .scheduler import (Scheduler)


def run_single(promise):
    """Evaluates a promise in single threaded mode."""
    Scheduler().run(
        Queue() >> worker,
        get_workflow(promise))
