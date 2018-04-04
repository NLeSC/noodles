from .dynamic_pool import DynamicPool, xenon_interactive_worker
from ..scheduler import Scheduler
from ..job_keeper import JobKeeper

from ...workflow import (get_workflow)

from copy import copy


def run_xenon_simple(workflow, machine, worker_config):
    """Run a workflow using a single Xenon remote worker.

    :param workflow: |Workflow| or |PromisedObject| to evaluate.
    :param machine: |Machine| instance.
    :param worker_config: Configuration for the pilot job."""
    scheduler = Scheduler()

    return scheduler.run(
        xenon_interactive_worker(machine, worker_config),
        get_workflow(workflow)
    )


def run_xenon(
        workflow, *, machine, worker_config, n_processes, deref=False,
        verbose=False):
    """Run the workflow using a number of online Xenon workers.

    :param workflow: |Workflow| or |PromisedObject| to evaluate.
    :param machine: The |Machine| instance.
    :param worker_config: Configuration of the pilot job
    :param n_processes: Number of pilot jobs to start.
    :param deref: Set this to True to pass the result through one more
        encoding and decoding step with object dereferencing turned on.
    :returns: the result of evaluating the workflow
    """

    dynamic_pool = DynamicPool(machine)

    for i in range(n_processes):
        cfg = copy(worker_config)
        cfg.name = 'xenon-{0:02}'.format(i)
        dynamic_pool.add_xenon_worker(cfg)

    job_keeper = JobKeeper()
    S = Scheduler(job_keeper=job_keeper, verbose=verbose)

    result = S.run(
        dynamic_pool, get_workflow(workflow)
    )

    dynamic_pool.close_all()

    if deref:
        return worker_config.registry().dereference(result, host='scheduler')
    else:
        return result
