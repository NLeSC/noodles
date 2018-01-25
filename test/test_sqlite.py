# import pytest

from noodles.prov.sqlite import JobDB
from noodles import serial
from noodles.tutorial import (sub, add)
from noodles.run.scheduler import Job


def test_add_job():
    db = JobDB(':memory:', registry=serial.base())

    wf = sub(1, 1)
    job = Job(wf._workflow, wf._workflow.root)
    key, node = db.register(job)
    msg, db_id, value = db.add_job_to_db(key, node)
    assert msg == 'initialized'

    duplicates = db.store_result_in_db(key, '0')
    assert duplicates == []

    key, node = db.register(job)
    msg, db_id, value = db.add_job_to_db(key, node)
    assert msg == 'retrieved'
    assert value == '0'


def test_attaching():
    db = JobDB(':memory:', registry=serial.base())

    wf = add(1, 1)
    job = Job(wf._workflow, wf._workflow.root)
    key1, node1 = db.register(job)
    msg, db_id, value = db.add_job_to_db(key1, node1)
    assert msg == 'initialized'

    key2, node2 = db.register(job)
    msg, db_id, value = db.add_job_to_db(key2, node2)
    assert msg == 'attached'
    assert db_id == key1

    duplicates = db.store_result_in_db(key1, '2')
    assert duplicates == [key2]

    key3, node3 = db.register(job)
    msg, db_id, value = db.add_job_to_db(key3, node3)
    assert msg == 'retrieved'
    assert value == '2'
