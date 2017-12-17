import noodles
from noodles import serial
from noodles.tutorial import add, mul
from noodles.run.xenon import (
    Machine, XenonJobConfig)
from noodles.run.messages import (
    JobMessage)

from pathlib import Path
import xenon
import socket
import sys


def test_machine_batch_job(xenon_server, tmpdir):
    m = Machine(scheduler_adaptor='local')
    scheduler = m.scheduler
    tmpdir = Path(str(tmpdir))

    stdout_file = Path(tmpdir) / 'hostname.txt'
    job_description = xenon.JobDescription(
        executable='/bin/hostname', stdout=str(stdout_file))
    job = scheduler.submit_batch_job(job_description)
    scheduler.wait_until_done(job)

    lines = [line.strip() for line in stdout_file.open()]
    assert lines[0] == socket.gethostname()

    scheduler.close()


def test_worker_one_batch_job(xenon_server, tmpdir):
    tmpdir = Path(str(tmpdir))
    infile = tmpdir / 'infile.json'
    outfile = tmpdir / 'outfile.json'

    wf = add(1, 1)
    job = next(iter(wf._workflow.nodes.values()))
    job_message = JobMessage(42, job)

    registry = serial.base()
    print(registry.to_json(job_message), file=infile.open('w'))

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
    assert result.status == 'done'
    assert result.key == 42
    assert result.msg is None
    assert result.value == 2

    scheduler.close()


def test_worker_one_online_job(xenon_server):
    wf = mul(6, 7)
    job = next(iter(wf._workflow.nodes.values()))
    job_message = JobMessage(1234, job)
    registry = serial.base()
    msg = registry.to_json(job_message)

    m = Machine(scheduler_adaptor='local')
    scheduler = m.scheduler

    job_config = XenonJobConfig()
    executable, arguments = job_config.command_line()

    xjob_description = xenon.JobDescription(
        executable=str(executable), arguments=arguments)

    xjob, xstdout = scheduler.submit_interactive_job(
        xjob_description, [msg.encode()])
    scheduler.wait_until_done(xjob)

    result_json = ''.join(m.stdout.decode() for m in xstdout if m.stdout)
    assert len(result_json) > 0

    result = registry.from_json(result_json)
    assert result.status == 'done'
    assert result.key == 1234
    assert result.msg is None
    assert result.value == 42

    scheduler.close()


def test_worker_ten_online_jobs(xenon_server):
    registry = serial.base()

    def single_job(wf):
        job = next(iter(wf._workflow.nodes.values()))
        job_message = JobMessage(0, job)
        return (registry.to_json(job_message) + '\n').encode()

    m = Machine(scheduler_adaptor='local')
    scheduler = m.scheduler

    job_config = XenonJobConfig(verbose=True)
    executable, arguments = job_config.command_line()

    xjob_description = xenon.JobDescription(
        executable=str(executable), arguments=arguments)

    xjob, xstdout = scheduler.submit_interactive_job(
        xjob_description, [single_job(mul(10, i)) for i in range(10)])
    scheduler.wait_until_done(xjob)

    result_json = ""
    for m in xstdout:
        if m.stdout:
            result_json += m.stdout.decode()
        if m.stderr:
            for l in m.stderr.decode().splitlines():
                print("remote:", l)

    results = [registry.from_json(r)
               for r in result_json.splitlines()]
    print("results: ", end='')
    for r in results:
        print(r.value, end=' ')
    print()

    assert len(results) == 10

    for i, result in enumerate(results):
        assert result.status == 'done'
        assert result.key == 0
        assert result.msg is None
        assert result.value == i * 10

    scheduler.close()
