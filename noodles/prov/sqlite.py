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
    the same "session" as the new job, the new job is marked link of the
    older one. We keep a note in memory that, when the result is known, it is
    also given for the newer job.
    3. Otherwise, we pass the job on to a worker and wait for the result.

In the case that a job returns a new workflow, we'd like to identify the result
of that workflow with that of the original job. In that case we add a "link"
once a non-workflow result is known.
"""

import sqlite3
from threading import Lock
from collections import (defaultdict)
from typing import NamedTuple
import datetime
import sys
from ..run.messages import (JobMessage, ResultMessage)
from ..workflow import (is_workflow, get_workflow)
from .key import (prov_key)

try:
    import ujson as json
except ImportError:
    import json


schema = '''
    create table if not exists "jobs" (
        "id"          integer unique primary key,
        "session"     integer not null references "sessions"("id")
                      on delete cascade,
        "name"        text,
        "prov"        text,
        "version"     text,
        "function"    text,
        "arguments"   text,
        "result"      text,
        "is_workflow" integer,
        "link"        integer references "jobs"("id") );

    create index if not exists "prov" on "jobs"("prov");

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


class JobEntry(NamedTuple):
    """Python tuple reflection of Job entry in database."""
    id: int
    session: int
    name: str
    prov: str
    version: str
    function: str
    arguments: str
    result: str
    is_workflow: int
    link: int


class SessionEntry(NamedTuple):
    """Python tuple reflection of Session entry in database."""
    id: int
    time: datetime.datetime
    info: str


class TimestampEntry(NamedTuple):
    """Python tuple reflection of Timestamp entry in database."""
    job: int
    time: datetime.datetime
    what: str


class JobDB:
    """Keeps a database of jobs, with a MD5 hash that encodes the function
    name, version, and all arguments to the function.
    """
    def __init__(self, path, registry, info=None):
        self.attached = defaultdict(list)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.jobs = {}
        self.links = defaultdict(list)
        self.registry = registry()

        self.cur = self.connection.cursor()
        self.cur.executescript(schema)
        self.lock = Lock()
        self.workflows = {}

        with self.lock:
            self.cur.execute(
                'insert into "sessions" ("info") values (?)', (info,))
            self.session = self.cur.lastrowid

    def __enter__(self):
        return self

    def __exit__(self, exc, exc_type, stacktrace):
        self.connection.commit()
        self.connection.close()

    # --------- job-keeper interface ------------
    def __len__(self):
        with self.lock:
            return len(self.jobs)

    def __delitem__(self, key):
        with self.lock:
            del self.jobs[key]

    def __getitem__(self, key):
        with self.lock:
            return self.jobs[key]

    def register(self, job):
        """Takes a job (unencoded) and adorns it with a unique key; this makes
        an entry in the database without any further specification."""
        with self.lock:
            self.cur.execute(
                'insert into "jobs" ("name", "session") values (?, ?)',
                (job.name, self.session))
            self.jobs[self.cur.lastrowid] = job
            return JobMessage(self.cur.lastrowid, job.node)

    def store_result(self, key, status, value, _):
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

    # --------- database interface ---------------------

    def add_job_to_db(self, key, job):
        """Add job info to the database."""
        job_msg = self.registry.deep_encode(job)
        prov = prov_key(job_msg)

        with self.lock:
            self.cur.execute(
                'select * from "jobs" where "prov" = ? '
                'and (("result" is not null) or '
                '("session" = ? and "link" is null))',
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

            if rec:
                self.cur.execute(
                    'update "jobs" set "link" = ? where "id" = ?',
                    (rec.id, key))

                if rec.result is not None and rec.is_workflow == 1:
                    if rec.link is not None:
                        self.cur.execute(
                            'select * from "jobs" where "id" = ?',
                            (rec.link,))
                        rec = self.cur.fetchone()
                        rec = JobEntry(*rec) if rec is not None else None
                    else:
                        self.attached[rec.id].append(key)
                        return 'attached', None

                if rec.result is not None:
                    result_value = self.registry.from_json(rec.result)
                    result = ResultMessage(
                        key, 'retrieved', result_value, None)
                    return 'retrieved', result

                if rec.session == self.session:
                    self.attached[rec.id].append(key)
                    return 'attached', None

            return 'initialized', None

    def job_exists(self, prov):
        """Check if a job exists in the database."""
        with self.lock:
            self.cur.execute('select * from "jobs" where "prov" = ?;', (prov,))
            rec = self.cur.fetchone()
            return rec is not None

    def store_result_in_db(self, result):
        """Store a result in the database."""
        result_value_msg = self.registry.to_json(result.value)
        with self.lock:
            self.cur.execute(
                'update "jobs" set "result" = ?, '
                '"is_workflow" = ? where "id" = ?;',
                (result_value_msg, is_workflow(result.value), result.key))

            workflow, node = self.jobs[result.key]
            attached_keys = ()

            if is_workflow(result.value):
                new_workflow_id = id(get_workflow(result.value))
                self.links[new_workflow_id].append(result.key)

                if node == workflow.root:
                    self.links[new_workflow_id].extend(
                        self.links[id(workflow)])
                    del self.links[id(workflow)]

            elif node == workflow.root:
                attached_keys = tuple(self.attached[result.key])
                del self.attached[result.key]

                linked_keys = tuple(self.links[id(workflow)])
                del self.links[id(workflow)]

                # update links for jobs up in the call-stack (parent workflows)
                n_questions = ','.join('?' * len(linked_keys))
                self.cur.execute(
                    'update "jobs" set "link" = ? where "id" in ({});'
                    .format(n_questions),
                    (result.key,) + linked_keys)

                # jobs that were attached to the parent workflow(s) will not
                # receive the current result automatically, so we need to force
                # feed them to the scheduler.
                for k in linked_keys:
                    attached_keys += tuple(self.attached[k])

            else:
                attached_keys = tuple(self.attached[result.key])
                del self.attached[result.key]

            return attached_keys

    def add_time_stamp(self, db_id, name):
        """Add a timestamp to the database."""
        with self.lock:
            self.cur.execute(
                'insert into "timestamps" ("job", "what")'
                'values (?, ?);', (db_id, name))
