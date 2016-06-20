import uuid
import time
import json
import sys

from threading import Lock
from .haploid import (sink_map, coroutine)

class JobKeeper(dict):
    def __init__(self, keep=True):
        super(JobKeeper, self).__init__()
        self.keep = keep
        self.lock = Lock()

    def register(self, job):
        with self.lock:
            key = uuid.uuid1()
            self[key] = job
        return key, job.node

    def __delitem__(self, key):
        pass

    def store_result(self, key, status, value, err):
        if status != 'done':
            return

        if key not in self:
            print("WARNING: store_result without previous job registration:\n" \
                  "   race condition? Not doing anything.\n", file=sys.stderr)
            return

        with self.lock:
            job = self[key]
            job.node.result = value


class JobTimer(dict):
    def __init__(self, timing_file, registry=None):
        super(JobTimer, self).__init__()
        if isinstance(timing_file, str):
            self.fo = open(timing_file, 'w')
        else:
            self.fo = timing_file
        #h self.registry = registry()

    def register(self, job):
        key = uuid.uuid1()
        job.sched_time = time.time()
        self[key] = job
        return key, job.node

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
                'description': job.node.hints['display'].format(**job.node.bound_args.arguments),
                'schedule_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(job.sched_time)),
                'start_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(job.start_time)),
                'done_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
                'run_duration': now - job.start_time }
            self.fo.write('{record},\n'.format(record=json.dumps(msg_obj, indent=2)))


