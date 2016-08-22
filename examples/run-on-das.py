from noodles import (
    serial, gather)

from noodles.run.xenon import (
    XenonConfig, RemoteJobConfig, XenonKeeper, run_xenon_prov)

from noodles.display import (
    NCDisplay)

from noodles.tutorial import (
    log_add, mul, sub, accumulate)

import os

if __name__ == '__main__':
    A = log_add(1, 1)
    B = sub(3, A)

    multiples = [mul(log_add(i, B), A) for i in range(6)]
    C = accumulate(gather(*multiples))

    with XenonKeeper() as Xe:
        certificate = Xe.credentials.newCertificateCredential(
            'ssh', os.environ["HOME"] + '/.ssh/id_rsa', '<username>', '', None)

        xenon_config = XenonConfig(
            jobs_scheme='slurm',
            location='<login-address>',
            credential=certificate,
            jobs_properties={
                'xenon.adaptors.slurm.ignore.version': 'true'
            }
        )

        job_config = RemoteJobConfig(
            registry=serial.base,
            prefix='<path-to-virtual-env>',
            working_dir='<project-path>',
            time_out=5000
        )

        with NCDisplay() as display:
            result = run_xenon_prov(
                C, Xe, "cache.json", 2,
                xenon_config, job_config, display=display)
        print("The answer is", result)
