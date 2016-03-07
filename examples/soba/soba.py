import noodles
from noodles.workflow import (get_workflow)
from noodles.run.local import (threaded_worker)
from noodles.run.coroutines import (Connection, coroutine_sink, siphon_source)
from noodles.run.experimental import (Logger)
from noodles.display import SimpleDisplay

from collections import namedtuple
import subprocess
import sys
import argparse
import json
import threading
import time


class Job:
    def __init__(self, task, exclude, state, job, key):
        self.task = task
        self.exclude = exclude
        self.state = state
        self.job = job
        self.key = key


def dynamic_exclusion_worker(display, n_threads):
    result_source, job_sink = threaded_worker(n_threads).setup()

    jobs = {}
    key_task = {}

    log = Logger()
    log_job = log.job_sink()
    log_result = log.result_sink()

    @coroutine_sink
    def pass_job():
        while True:
            key, job = yield

            if (job.hints and 'exclude' in job.hints):
                j = Job(task=job.hints['task'],
                        exclude=job.hints['exclude'],
                        state='waiting',
                        job=job,
                        key=key)
                jobs[j.task] = j
                key_task[key] = j.task
                try_to_start(j.task)

            else:
                log_job.send((key, job))
                job_sink.send((key, job))

    def is_not_running(task):
        return not (task in jobs and jobs[task].state == 'running')

    def try_to_start(task):
        if jobs[task].state != 'waiting':
            return

        if all(is_not_running(i) for i in jobs[task].exclude):
            jobs[task].state = 'running'
            key, job = jobs[task].key, jobs[task].job
            log_job.send((key, job))
            job_sink.send((key, job))

    def finish(key):
        task = key_task[key]
        jobs[task].state = 'done'
        for i in jobs[task].exclude:
            try_to_start(i)

    def pass_result():
        for key, status, result, err in result_source:
            if key in key_task:
                finish(key)

            log_result.send((key, status, result, err))
            yield (key, status, result, err)

    t_log = threading.Thread(target=display, args=(log,))
    t_log.daemon = True
    t_log.start()

    return Connection(pass_result, pass_job)


def run(wf, *, display, n_threads=1):
    worker = dynamic_exclusion_worker(display, n_threads)
    return noodles.Scheduler(error_handler=display.error_handler)\
        .run(worker, get_workflow(wf))


@noodles.schedule_hint(display='{task}', confirm=True)
def system_command(cmd, task):
    time.sleep(0.5)
    p = subprocess.run(
        cmd, stderr=subprocess.PIPE, universal_newlines=True)
    p.check_returncode()
    return 0


def make_job(cmd, task_id, exclude):
    j = system_command(cmd, task_id)
    noodles.update_hints(j, {'task': str(task_id),
                             'exclude': [str(x) for x in exclude]})
    return j


def error_filter(xcptn):
    if isinstance(xcptn, subprocess.CalledProcessError):
        return xcptn.stderr
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SOBA: Run a non-directional exclusion graph job.")
    parser.add_argument(
        '-j', dest='n_threads', type=int, default=1,
        help='number of threads to run simultaneously.')
    parser.add_argument(
        '-dumb', default=False, action='store_true',
        help='print info without special term codes.')
    parser.add_argument(
        'target', type=str,
        help='a JSON file specifying the graph.')
    args = parser.parse_args(sys.argv[1:])

    input = json.load(open(args.target, 'r'))
    jobs = [make_job(['echo', '--> ', str(td['command'].split()), '<--'],
                     td['task'], td['exclude']) for td in input]
    wf = noodles.gather(*jobs)
    with SimpleDisplay(error_filter) as display:
        run(wf, display=display, n_threads=args.n_threads)
