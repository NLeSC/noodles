import docker
import os
import stat
import json
import sys
import uuid
import subprocess
import time


def build_image(client: docker.Client, path='./remote-docker', name='noodles-remote'):
    """Build the Docker image as per Dockerfile present in the 'remote-docker'
    sub-directory. This Docker image should suffice to emulate a remote machine
    with SLURM queue manager and ssh/sftp connection installed. If the docker image
    with given name is newer than the Dockerfile, nothing is done.

    :param client:
        Docker client
    :param path:
        Location of Dockerfile
    :param name:
        Name of the image
    """
    assert os.path.exists(path + '/Dockerfile')
    time = os.stat(path + '/Dockerfile').st_mtime

    il = client.images(name=name)
    if len(il) == 0 or il[0]['Created'] < time:
        response = client.build(path, tag=name, rm=True)
        for json_bytes in response:
            line = json.loads(json_bytes.decode())['stream']
            print(line, end='', file=sys.stderr, flush=True)


def reset_container(client: docker.Client, session, n=0, image='noodles-remote'):
    host_config = client.create_host_config(port_bindings={22: (10022 + n*100)})
    container = client.create_container(
        image=image, host_config=host_config, labels={'noodles': str(n), 'session': session})
    client.start(container)
    time.sleep(0.5)
    return container


def clean_up(client, session):
    cl = client.containers(
        all=True, filters={'label': 'session={}'.format(session)})

    for c in cl:
        client.stop(c, 0)
        client.remove_container(c)


class Container:
    def __init__(self, client, session, n):
        self.client = client
        self.session = session
        self.n = n

    def __enter__(self):
        reset_container(self.client, self.session, self.n)

    def __exit__(self, exc_type, exc_val, exc_tb):
        clean_up(self.client, self.session)


def test_docker_sanity():
    path = './remote-docker'
    os.chmod(path + '/id_rsa', stat.S_IRUSR)
    docker_client = docker.Client()
    session = str(uuid.uuid4())
    build_image(docker_client, path)

    with Container(docker_client, session, 0):
        subprocess.run(['ssh', '-i', path + '/id_rsa', '-p', '10022',
                        'joe@0.0.0.0', 'touch hello.txt'])
        p = subprocess.run(['ssh', '-i', path + '/id_rsa', '-p', '10022',
                            'joe@0.0.0.0', 'ls'], stdout=subprocess.PIPE)
        assert p.stdout.decode().split()[0] == 'hello.txt'

