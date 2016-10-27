import uuid
import time
import json
import sys

from threading import Lock
from .haploid import (coroutine)
from .messages import (JobMessage)


class JobKeeper(dict):
    def __init__(self, keep=False):
        super(JobKeeper, self).__init__()
        self.keep = keep
        self.lock = Lock()
        self.workflows = {}

    def register(self, job):
        with self.lock:
            key = str(uuid.uuid4())
            job.log = []
            job.log.append((time.time(), 'register', None, None))
            self[key] = job

        return JobMessage(key, job.node)

    def __delitem__(self, key):
        if not self.keep:
            super(JobKeeper, self).__delitem__(key)

    def store_result(self, key, status, value, err):
        if status != 'done':
            return

        if key not in self:
            print("WARNING: store_result called but job not in registry:\n"
                  "   race condition? Not doing anything.\n", file=sys.stderr)
            return

        with self.lock:
            job = self[key]
            job.node.result = value

    @coroutine
    def message(self):
        while True:
            key, status, value, err = yield

            with self.lock:
                if key not in self:
                    continue

                job = self[key]
                job.log.append((time.time(), status, value, err))


class JobTimer(dict):
    def __init__(self, timing_file, registry=None):
        super(JobTimer, self).__init__()
        self.workflows = {}

        if isinstance(timing_file, str):
            self.fo = open(timing_file, 'w')
            self.owner = True
        else:
            self.fo = timing_file
            self.owner = False

    def register(self, job):
        key = str(uuid.uuid4())
        job.sched_time = time.time()
        self[key] = job
        return JobMessage(key, job.node)

    def __delitem__(self, key):
        pass

    # def message(self, key, status, value, err):
    @coroutine
    def message(self):
        while True:
            key, status, value, err = yield
            if hasattr(self, status):
                getattr(self, status)(key, value, err)

    def start(self, key, value, err):
        self[key].start_time = time.time()

    def done(self, key, value, err):
        job = self[key]
        now = time.time()
        if job.node.hints and 'display' in job.node.hints:
            msg_obj = {
                'description': job.node.hints['display'].format(
                    **job.node.bound_args.arguments),
                'schedule_time': time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ', time.gmtime(job.sched_time)),
                'start_time': time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ', time.gmtime(job.start_time)),
                'done_time': time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
                'run_duration': now - job.start_time}
            self.fo.write('{record},\n'.format(record=json.dumps(
                msg_obj, indent=2)))

    def __enter__(self):
        return self

    def __exit__(self, e_type, e_value, e_tb):
        if self.owner:
            self.fo.close()
