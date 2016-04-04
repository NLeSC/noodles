from noodles import (
    serial, gather)

from noodles.run.xenon import (
    XenonConfig, RemoteJobConfig, XenonKeeper, run_xenon)

from noodles.tutorial import (
    add, mul, sub, accumulate)

import os

if __name__ == '__main__':
    A = add(1, 1)
    B = sub(3, A)

    multiples = [mul(add(i, B), A) for i in range(6)]
    C = accumulate(gather(*multiples))

    with XenonKeeper() as Xe:
        certificate = Xe.credentials.newCertificateCredential(
            'ssh', os.environ["HOME"] + '/.ssh/id_rsa', '<username>', '', None)

        xenon_config = XenonConfig(
            jobs_scheme='slurm',
            location=None,
            # credential=certificate
        )

        job_config = RemoteJobConfig(
            registry=serial.base,
            prefix='/home/jhidding/venv',
            working_dir='/home/jhidding/noodles',
            time_out=1
        )

        result = run_xenon(Xe, 2, xenon_config, job_config, C)
        print("The answer is", result)

