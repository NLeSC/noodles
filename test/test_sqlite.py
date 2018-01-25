# import pytest

from noodles.prov.sqlite import JobDB
from noodles import serial
from noodles.tutorial import (sub, add)
from noodles.run.scheduler import Job
from noodles.run.messages import (ResultMessage)


def test_add_job():
    db = JobDB(':memory:', registry=serial.base)

    wf = sub(1, 1)
    job = Job(wf._workflow, wf._workflow.root)
    key, node = db.register(job)
    msg, value = db.add_job_to_db(key, node)
    assert msg == 'initialized'

    duplicates = db.store_result_in_db(ResultMessage(key, 'done', 0, None))
    assert duplicates == ()

    key, node = db.register(job)
    msg, result = db.add_job_to_db(key, node)
    assert msg == 'retrieved'
    assert result.value == 0


def test_attaching():
    db = JobDB(':memory:', registry=serial.base)

    wf = add(1, 1)
    job = Job(wf._workflow, wf._workflow.root)
    key1, node1 = db.register(job)
    msg, value = db.add_job_to_db(key1, node1)
    assert msg == 'initialized'

    key2, node2 = db.register(job)
    msg, value = db.add_job_to_db(key2, node2)
    assert msg == 'attached'

    duplicates = db.store_result_in_db(ResultMessage(key1, 'done', 2, None))
    assert duplicates == (key2,)

    key3, node3 = db.register(job)
    msg, result = db.add_job_to_db(key3, node3)
    assert msg == 'retrieved'
    assert result.value == 2
