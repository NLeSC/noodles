from .dynamic_pool import DynamicPool, xenon_interactive_worker
from ..scheduler import Scheduler
from ..job_keeper import JobKeeper
from ..haploid import (broadcast, sink_map, patch, branch)
from ..queue import Queue

from ...workflow import (get_workflow)

import threading
from copy import copy


def run_xenon_simple(wf, machine, worker_config):
    S = Scheduler()

    result = S.run(
        xenon_interactive_worker(machine, worker_config), get_workflow(wf)
    )

    return result


def run_xenon(wf, machine, n_processes, worker_config, *, deref=False, job_keeper=None):
    """Run the workflow using a number of online Xenon workers.

    :param Xe:
        The XenonKeeper instance.

    :param wf:
        The workflow.
    :type wf: `Workflow` or `PromisedObject`

    :param n_processes:
        Number of processes to start.

    :param xenon_config:
        The :py:class:`XenonConfig` object that gives tells us how to use
        Xenon.

    :param job_config:
        The :py:class:`RemoteJobConfig` object that specifies the command to
        run remotely for each worker.

    :param deref:
        Set this to True to pass the result through one more encoding and
        decoding step with object derefencing turned on.
    :type deref: bool

    :returns: the result of evaluating the workflow
    :rtype: any
    """

    DP = DynamicPool(machine)

    for i in range(n_processes):
        cfg = copy(worker_config)
        cfg.name = 'xenon-{0:02}'.format(i)
        DP.add_xenon_worker(cfg)

    if job_keeper is None:
        job_keeper = JobKeeper()
    S = Scheduler(job_keeper=job_keeper)

    result = S.run(
        DP, get_workflow(wf)
    )

    if deref:
        return job_config.registry().dereference(result, host='scheduler')
    else:
        return result
