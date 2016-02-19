from noodles.run.xenon import (XenonJob, XenonScheduler, XenonKeeper, XenonConfig)

import docker
import uuid
import subprocess
import os
import stat

from .test_docker import (Container)

# path to docker and rsa-key, ensure the key has correct access rights
path = './remote-docker'
os.chmod(path + '/id_rsa', stat.S_IRUSR)


def perform_submission(x: XenonKeeper, config: XenonConfig):
    session = str(uuid.uuid4())
    docker_client = docker.Client()

    with Container(docker_client, session, 0):
        s = XenonScheduler(x, config)

        s.submit(['/bin/bash', '-c', 'echo "Hello World!" > hello.txt'],
                 interactive=False).wait_until_done(1000)

        p = subprocess.run(['ssh', '-i', path + '/id_rsa', '-p', '10022',
                            'joe@0.0.0.0', '-t', 'cat hello.txt'],
                           stdout=subprocess.PIPE)

        result = p.stdout.decode().split('\n')[0].strip()
        assert result == 'Hello World!'


def test_ssh_job_submission():
    with XenonKeeper() as x:
        certificate = x.credentials.newCertificateCredential(
            'ssh', path + '/id_rsa', 'joe', '', None)

        config = XenonConfig(
            jobs_scheme='ssh',
            location='0.0.0.0:10022',
            credential=certificate)

        perform_submission(x, config)


def test_slurm_job_submission():
    with XenonKeeper() as x:
        certificate = x.credentials.newCertificateCredential(
            'ssh', path + '/id_rsa', 'joe', '', None)

        config = XenonConfig(
            jobs_scheme='slurm',
            location='0.0.0.0:10022',
            credential=certificate,
            jobs_properties={'xenon.adaptors.slurm.ignore.version': 'true'})

        perform_submission(x, config)
