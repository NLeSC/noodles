import docker
import os
import json
import sys

docker_client = docker.Client()


def build_image(path='./remote-docker', tag='noodles-remote'):
    """Build the Docker image as per Dockerfile present in the 'remote-docker'
    sub-directory. This Docker image should suffice to emulate a remote machine
    with SLURM queue manager and ssh/sftp connection installed.

    :param path:
        Location of Dockerfile
    :param tag:
        Name of the image
    """
    assert os.path.exists(path + '/Dockerfile')

    response = docker_client.build(path, tag=tag, rm=True)
    for json_bytes in response:
        line = json.loads(json_bytes.decode())['stream']
        print(line, end='', file=sys.stderr, flush=True)

