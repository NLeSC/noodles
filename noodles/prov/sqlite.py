import sqlite3
from threading import Lock
from collections import (namedtuple, defaultdict)
# from ..utility import on
import time
import sys
from ..run.messages import (JobMessage)
from .key import (prov_key)

try:
    import ujson as json
except ImportError:
    import json


schema = '''
    create table if not exists "jobs" (
        "id"        integer unique primary key,
        "run"       integer not null references "runs"("id")
                    on delete cascade,
        "name"      text,
        "prov"      text,
        "duplicate" integer,
        "version"   text,
        "function"  text,
        "arguments" text,
        "result"    text );

    create table if not exists "runs" (
        "id"        integer unique primary key,
        "time"      datetime default current_timestamp,
        "info"      text );

    create table if not exists "timestamps" (
        "job"       integer not null references "jobs"("id")
                    on delete cascade,
        "time"      datetime default current_timestamp,
        "what"      text );
'''

JobEntry = namedtuple(
        'JobEntry',
        ['id', 'run', 'name', 'prov', 'link', 'duplicate',
         'version', 'function', 'arguments', 'result'])

RunEntry = namedtuple(
        'RunEntry'
        ['id', 'time', 'info'])

TimestampEntry = namedtuple(
        'TimestampEntry',
        ['job', 'time', 'what'])


def time_stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time()))


class JobDB:
    """Keeps a database of jobs, with a MD5 hash that encodes the function
    name, version, and all arguments to the function.
    """
    def __init__(self, path, registry, info=None):
        self.duplicates = defaultdict(list)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.jobs = {}
        self.links = {}
        self.registry = registry

        self.cur = self.connection.cursor()
        self.cur.executescript(schema)
        self.lock = Lock()

        with self.lock:
            self.cur.execute('insert into "runs" ("info") values (?)', info)
            self.run = self.cur.lastrowid

    # --------- job-keeper interface ------------

    def __delitem__(self, key):
        del self.jobs[key]

    def __getitem__(self, key):
        return self.jobs[key]

    def register(self, job):
        """Takes a job (unencoded) and adorns it with a unique key; this makes
        an entry in the database without any further specification."""
        with self.lock:
            self.cur.execute(
                'insert into "jobs" ("name") values (?)', job.name)
            self.jobs[self.cur.lastrowid] = job
            return JobMessage(self.cur.lastrowid, job.node)

    def store_result(self, key, status, value, err):
        """Store the result of a job back in the node; this does nothing to the
        database."""
        if status != 'done':
            return

        if key not in self.jobs:
            print("WARNING: store_result called but job not in registry:\n"
                  "   race condition? Not doing anything.\n", file=sys.stderr)
            return

        with self.lock:
            job = self.jobs[key]
            job.node.result = value

    def add_link(self, db_id, ppn):
        with self.lock:
            self.links[db_id] = ppn

    # --------- database interface ---------------------

    def add_job_to_db(self, key, job):
        """Add job info to the database."""
        job_msg = self.registry.deep_encode(job)
        prov = prov_key(job_msg)

        with self.lock:
            self.cur.execute(
                'select * from "jobs" where "prov" = ? '
                'and (("result" is not null) or '
                '("run" = ? and "duplicate" is none))',
                (prov, self.run))
            rec = self.cur.fetchone()
            rec = JobEntry(existing) if existing is not None else None

            self.cur.execute(
                'update "jobs" set "prov" = ?, "version" = ?, "function" = ?, '
                '"arguments" = ? where "id" = ?',
                (prov, job_msg['data']['hints'].get('version'),
                 json.dumps(job_msg['data']['function']),
                 json.dumps(job_msg['data']['arguments']),
                 key))

            if rec:
                self.cur.execute(
                    'update "jobs" set "duplicate" = ? where "id" = ?',
                    (existing.id, key))

            if rec.result is not None:
                return 'retrieved', rec.id, rec.result

            job_running = rec and rec.key in self
            wf_running = rec and rec.key in self.links

            if job_running or wf_running:
                self.duplicates[rec.id].append(rec.key)
                return 'attached', rec.id, None

            return 'broken', None, None

    def job_exists(self, prov):
        with self.lock:
            self.cur.execute('select * from "jobs" where "prov" = ?;', (prov,))
            rec = self.cur.fetchone()
            return rec is not None

    def store_result_in_db(self, db_id, result):
        with self.lock:
            self.add_time_stamp(db_id, 'done')
            self.cur.execute(
                'update "jobs" set "result" = ? where "id" = ?;',
                (result, db_id))
            # self.cur.execute('select "duplicate" from "duplicates" where
            # "primary" = ?;', db_id)
            # duplicates = self.cur.fetchall()
            return self.duplicates[db_id]

    def add_time_stamp(self, db_id, name):
        with self.lock:
            self.cur.execute(
                'insert into "timestamps" ("job", "what")'
                'values (?, ?)',
                (db_id, name))
