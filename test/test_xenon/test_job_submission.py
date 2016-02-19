import xenon
from noodles.run.xenon import (XenonJob, XenonKeeper, XenonConfig)

import docker
import uuid
from .test_docker import (Container)


# def test_job_submission():
#     session = str(uuid.uuid4())
#     docker_client = docker.Client()
#     with Container(docker_client, session, 0):
#         certificate = xenon.credentials.
#         config = XenonConfig(
#             jobs_scheme='ssh',
#             location='0.0.0.0',)
