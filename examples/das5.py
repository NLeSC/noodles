from noodles.run.xenon import (
    Machine, XenonJobConfig, run_xenon)
from noodles import gather_all, schedule
from noodles.tutorial import (add, sub, mul)
import xenon
from pathlib import Path


def test_xenon_42_multi():
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = schedule(sum)(gather_all(multiples))

    machine = Machine(
        scheduler_adaptor='slurm',
        location='ssh://fs0.das5.cs.vu.nl/home/jhidding',
        credential=xenon.CertificateCredential(
            username='jhidding',
            certfile='/home/johannes/.ssh/id_rsa'),
        jobs_properties={
            'xenon.adaptors.schedulers.ssh.strictHostKeyChecking': 'false'}
        )
    worker_config = XenonJobConfig(
        prefix=Path('/home/jhidding/.local/share/workon/mcfly'),
        working_dir='/home/jhidding/', time_out=1000000000000,
        verbose=False)  # , options=['-C', 'TitanX', '--gres=gpu:1'])

    result = run_xenon(
        C, machine=machine, worker_config=worker_config,
        n_processes=2)

    print("The answer is:", result)


xenon.init()
test_xenon_42_multi()
