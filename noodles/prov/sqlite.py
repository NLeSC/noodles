"""
SQLite3 job database
--------------------

The database contains three tables:
    - jobs
    - sessions
    - timestamps

Each job that is started will get an entry in the "jobs" table.
    1. If a job with the same "prov" field exists and it has a result, we mark
    the new job by identifying the existing result in the "link" field.
    2. If a job with the same "prov" field exists, but has no result and has
    the same "session" as the new job, the new job is marked duplicate of the
    older one. We keep a note in memory that, when the result is known, it is
    also given for the newer job.
    3. Otherwise, we pass the job on to a worker and wait for the result.

In the case that a job returns a new workflow, we'd like to identify the result
of that workflow with that of the original job. In that case we add a "link"
once a non-workflow result is known.
"""

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
        "session"   integer not null references "sessions"("id")
                    on delete cascade,
        "name"      text,
        "prov"      text,
        "link"      integer references "jobs"("id"),
        "version"   text,
        "function"  text,
        "arguments" text,
        "result"    text );

    create index "prov" on "jobs"("prov");

    create table if not exists "sessions" (
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
        ['id', 'session', 'name', 'prov', 'link',
         'version', 'function', 'arguments', 'result'])

SessionEntry = namedtuple(
        'SessionEntry',
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
            self.cur.execute('insert into "sessions" ("info") values (?)', (info,))
            self.session = self.cur.lastrowid

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
                'insert into "jobs" ("name", "session") values (?, ?)', (job.name, self.session))
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
        """Link the result of `ppn` to the job `db_id`."""
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
                '("session" = ? and "duplicate" is null))',
                (prov, self.session))
            rec = self.cur.fetchone()
            rec = JobEntry(*rec) if rec is not None else None

            self.cur.execute(
                'update "jobs" set "prov" = ?, "version" = ?, "function" = ?, '
                '"arguments" = ? where "id" = ?',
                (prov, job_msg['data']['hints'].get('version'),
                 json.dumps(job_msg['data']['function']),
                 json.dumps(job_msg['data']['arguments']),
                 key))

            print('found: ', rec)

            if rec:
                if rec.result is not None:
                    self.cur.execute(
                        'update "jobs" set "link" = ? where "id" = ?',
                        (rec.id, key))

                    return 'retrieved', rec.id, rec.result

                if rec.session == self.session:
                    self.cur.execute(
                        'update "jobs" set "link" = ? where "id" = ?',
                        (rec.id, key))
                    self.duplicates[rec.id].append(key)
                    return 'attached', rec.id, None

            return 'initialized', key, None


    def job_exists(self, prov):
        with self.lock:
            self.cur.execute('select * from "jobs" where "prov" = ?;', (prov,))
            rec = self.cur.fetchone()
            return rec is not None

    def store_result_in_db(self, db_id, result):
        with self.lock:
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
