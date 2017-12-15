import noodles
from noodles import serial
from noodles.run.xenon import (
    Machine, XenonJobConfig)

from pathlib import Path
import xenon
import socket
import sys


def test_machine_batch_job(xenon_server, tmpdir):
    m = Machine(scheduler_adaptor='local')
    scheduler = m.scheduler

    stdout_file = Path(tmpdir) / 'hostname.txt'
    job_description = xenon.JobDescription(
        executable='/bin/hostname', stdout=str(stdout_file))
    job = scheduler.submit_batch_job(job_description)
    scheduler.wait_until_done(job)

    lines = [line.strip() for line in stdout_file.open()]
    assert lines[0] == socket.gethostname()

    scheduler.close()


@noodles.schedule
def add(a, b):
    return a + b


def test_worker_one_job(xenon_server, tmpdir):
    infile = Path(tmpdir) / 'infile.json'
    outfile = Path(tmpdir) / 'outfile.json'

    wf = add(1, 1)
    print(wf._workflow.nodes)
    job = next(iter(wf._workflow.nodes.values()))
    registry = serial.base()
    print(registry.to_json(job), file=infile.open('w'))

    m = Machine(scheduler_adaptor='local')
    scheduler = m.scheduler

    job_config = XenonJobConfig()
    executable, arguments = job_config.command_line()

    job_description = xenon.JobDescription(
        executable=str(executable), arguments=arguments,
        stdin=str(infile), stdout=str(outfile))

    job = scheduler.submit_batch_job(job_description)
    scheduler.wait_until_done(job)

    result_json = [line.strip() for line in outfile.open()]
    assert len(result_json) == 1

    result = registry.from_json(result_json[0])
    print(result)

    scheduler.close()
