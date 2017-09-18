# import pytest

from noodles.prov.sqlite import JobDB
from noodles.prov.key import prov_key
from noodles import serial
from noodles.tutorial import (sub)
from noodles.run.job_keeper import JobKeeper
from noodles.run.scheduler import Job


def test_add_job():
    registry = serial.base()

    wf = sub(1, 1)

    jobs = JobKeeper()

    job = Job(wf._workflow, wf._workflow.root)
    key, node = jobs.register(job)
    job_msg = registry.deep_encode(node)
    print('job: ', job_msg)
    result_msg = registry.deep_encode(0)
    print('result: ', result_msg)
    prov = prov_key(job_msg)
    print('prov :', prov)

    db = JobDB(':memory:')
    msg, db_id, value = db.add_job(prov, job_msg, jobs)
    print(msg, db_id, value)
