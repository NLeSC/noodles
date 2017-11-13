from .dynamic_pool import DynamicPool
from ..scheduler import Scheduler
from ..job_keeper import JobKeeper
from ..haploid import (broadcast, sink_map, patch, branch)
from ..queue import Queue

from ...workflow import (get_workflow)

import threading
from copy import copy

# Only define run_xenon_prov if provenance is installed
try:
    from ..run_with_prov import prov_wrap_connection
except ImportError:
    pass
else:
    def run_xenon_prov(wf, Xe, jobdb_file, n_processes, xenon_config,
                       job_config, *, deref=False, job_keeper=None,
                       display=None):
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
            The :py:class:`RemoteJobConfig` object that specifies the command
            to run remotely for each worker.

        :param deref:
            Set this to True to pass the result through one more encoding and
            decoding step with object derefencing turned on.
        :type deref: bool

        :returns: the result of evaluating the workflow
        :rtype: any
        """
        DP = DynamicPool(Xe, xenon_config)

        for i in range(n_processes):
            cfg = copy(job_config)
            cfg.name = 'xenon-{0:02}'.format(i)
            DP.add_xenon_worker(cfg)

        if job_keeper is None:
            job_keeper = JobKeeper()
        S = Scheduler(job_keeper=job_keeper)

        LogQ = Queue()
        if display:
            tgt = broadcast(job_keeper.message, sink_map(display))
        else:
            tgt = job_keeper.message

        threading.Thread(
            target=patch,
            args=(LogQ.source, tgt),
            daemon=True).start()

        result = S.run(
            prov_wrap_connection(
                DP >> branch(LogQ.sink),
                DP.result_queue, job_config.registry,
                jobdb_file, job_keeper,
                log_q=LogQ),
            get_workflow(wf))

        if deref:
            return job_config.registry().dereference(result, host='localhost')
        else:
            return result


def run_xenon(wf, Xe, jobdb_file, n_processes, xenon_config,
              job_config, *, deref=False, job_keeper=None):
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

    DP = DynamicPool(Xe, xenon_config)

    for i in range(n_processes):
        cfg = copy(job_config)
        cfg.name = 'xenon-{0:02}'.format(i)
        DP.add_xenon_worker(cfg)

    if job_keeper is None:
        job_keeper = JobKeeper()
    S = Scheduler(job_keeper=job_keeper)

    # results = Queue()

    # LogQ = Queue()
    # if display:
    #     tgt = broadcast(job_keeper.message, sink_map(display))
    # else:
    #     tgt = job_keeper.message
    #
    # threading.Thread(
    #     target=patch,
    #     args=(LogQ.source, tgt),
    #     daemon=True).start()

    result = S.run(
        DP, get_workflow(wf)
    )
    # result = S.run(
    #     prov_wrap_connection(
    #         DP >> branch(LogQ.sink),
    #         results, job_config.registry,
    #         jobdb_file, job_keeper,
    #         log_q=LogQ),
    #     get_workflow(wf))

    if deref:
        return job_config.registry().dereference(result, host='localhost')
    else:
        return result
