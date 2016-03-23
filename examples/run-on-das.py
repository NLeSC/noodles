from noodles import (
    serial, gather)

from noodles.run.scheduler import (
    Scheduler)

from noodles.run.xenon import (
    XenonConfig, RemoteJobConfig,
    XenonKeeper, XenonScheduler,
    xenon_interactive_worker)

from noodles.run.hybrid import (
    hybrid_threaded_worker)

from noodles.workflow import (
    get_workflow)

from noodles.tutorial import (
    add, mul, sub, accumulate)

import copy
import random
import os


def run_xenon(Xe, n_processes, xenon_config, job_config, wf, deref=False):
    XeS = XenonScheduler(Xe, xenon_config)

    workers = {}
    for i in range(n_processes):
        cfg = copy.copy(job_config)
        cfg.name = 'remote-{0:02}'.format(i)
        new_worker = xenon_interactive_worker(XeS, cfg)
        workers[new_worker.name] = new_worker

    worker_names = list(workers.keys())

    def random_selector(_):
        return random.choice(worker_names)

    master_worker = hybrid_threaded_worker(random_selector, workers)
    result = Scheduler().run(master_worker, get_workflow(wf))

    if deref:
        return job_config.registry().dereference(result, host='localhost')
    else:
        return result


if __name__ == '__main__':
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(gather(*multiples))

    with XenonKeeper() as Xe:
        certificate = Xe.credentials.newCertificateCredential(
            'ssh', os.environ["HOME"] + '/.ssh/id_rsa', 'jhidding', '', None)

        xenon_config = XenonConfig(
            jobs_scheme='slurm',
            location='fs0.das5.cs.vu.nl',
            credential=certificate
        )

        job_config = RemoteJobConfig(
            registry=serial.base,
            prefix='/home/jhidding/venv',
            working_dir='/home/jhidding/noodles',
            time_out=1
        )

        result = run_xenon(Xe, 2, xenon_config, job_config, C)
        print("The answer is", result)
