from .coroutines import coroutine_sink, Connection
# from .run_common import Schedule
import xenon
import os
import time
from queue import Queue


def xenon_worker(poll_delay=1):
    xenon.init()

    x = xenon.Xenon()
    jobs_api = x.jobs()

    new_jobs = Queue()

    @coroutine_sink
    def send_job():
        sched = jobs_api.newScheduler('ssh', 'localhost', None, None)

        while True:
            key, job = yield
            desc = xenon.jobs.JobDescription()
            desc.setExecutable('python3.5')
            desc.setStdout(os.getcwd() + '/out.json')

            # submit a job
            job = jobs_api.submitJob(sched, desc)
            new_jobs.put((key, job))

    def get_result():
        jobs = {}

        while True:
            time.sleep(poll_delay)
            for key, job in jobs.items():
                ...
                result = 42
                yield (key, result)

            # put recently submitted jobs into the jobs-dict.
            while not new_jobs.empty():
                key, job = new_jobs.get()
                jobs[key] = job
                new_jobs.task_done()

    return Connection(get_result, send_job)
