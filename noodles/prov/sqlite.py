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
# from typing import NamedTuple
from collections import (namedtuple)
# import datetime
import sys
from enum import IntEnum

from ..run.messages import (JobMessage, ResultMessage)
from ..workflow import (is_workflow, get_workflow, FunctionNode, NodeData)
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
        "status"      integer references "status"("id"),
        "prov"        text,
        "version"     text,
        "function"    text,
        "arguments"   text,
        "result"      text,
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

    create table if not exists "status" (
        "id"        integer unique primary key,
        "name"      text );

    insert or ignore into "status" values
        (0, "INACTIVE"),    -- just barely known about
        (1, "WAITING"),     -- fully registered but no result yet
        (2, "STORED"),      -- the result of the job is stored
        (3, "WORKFLOW"),    -- the result of the job was a workflow
        (4, "DUPLICATE"),   -- the job was a duplicate
        (5, "LINKEE");      -- the job was not registered, but its result is
                            -- stored, because a linked job is registered
'''


JobEntry = namedtuple('JobEntry', [
    'id', 'session', 'name', 'status', 'prov', 'version', 'function',
    'arguments', 'result', 'link'])


# class JobEntry(NamedTuple):
#     """Python tuple reflection of Job entry in database."""
#     id: int
#     session: int
#     name: str
#     status: int
#     prov: str
#     version: str
#     function: str
#     arguments: str
#     result: str
#     link: int

SessionEntry = namedtuple('SessionEntry', [
    'id', 'time', 'info'])

# class SessionEntry(NamedTuple):
#     """Python tuple reflection of Session entry in database."""
#     id: int
#     time: datetime.datetime
#     info: str

TimestampEntry = namedtuple('TimestampEntry', [
    'job', 'time', 'what'])

# class TimestampEntry(NamedTuple):
#     """Python tuple reflection of Timestamp entry in database."""
#     job: int
#     time: datetime.datetime
#     what: str


class Status(IntEnum):
    INACTIVE = 0
    WAITING = 1
    STORED = 2
    WORKFLOW = 3
    DUPLICATE = 4
    LINKEE = 5


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
                'insert into "jobs" ("name", "session", "status") '
                'values (?, ?, ?)', (job.name, self.session, Status.INACTIVE))
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
    def list_jobs(self):
        with self.lock:
            self.cur.execute(
                'select "id", "function", "arguments" from "jobs"')
            return {
                x[0]: FunctionNode.from_node_data(NodeData(
                    self.registry.from_json(x[1]),
                    self.registry.from_json(x[2]),
                    {}
                )) for x in self.cur.fetchall()}

    def get_result(self, db_id):
        with self.lock:
            self.cur.execute(
                'select * from "jobs" where "id" = ?',
                (db_id,))
            rec = self.cur.fetchone()
            if rec is None:
                raise ValueError("No record found with id %s", db_id)
            rec = JobEntry(*rec)

            if rec.result is not None and rec.status == Status.WORKFLOW:
                # the found duplicate returned a workflow
                if rec.link is not None:
                    # link is set, so result is fully realized
                    self.cur.execute(
                        'select * from "jobs" where "id" = ?',
                        (rec.link,))
                    rec = self.cur.fetchone()
                    assert rec is not None, "database integrity violation"
                    rec = JobEntry(*rec)

                else:
                    # link is not set, the result is still waited upon
                    raise ValueError("Result for this job is not available.")

            assert rec.result is not None, "no result found"
            # result is found! return it
            result_value = self.registry.from_json(rec.result, deref=True)
            return result_value

    def add_job_to_db(self, key, job):
        """Add job info to the database."""
        job_msg = self.registry.deep_encode(job)
        prov = prov_key(job_msg)

        def set_link(duplicate_id):
            self.cur.execute(
                'update "jobs" set "link" = ?, "status" = ? where "id" = ?',
                (duplicate_id, Status.DUPLICATE, key))

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
                '"arguments" = ?, "status" = ? where "id" = ?',
                (prov, job_msg['data']['hints'].get('version'),
                 json.dumps(job_msg['data']['function']),
                 json.dumps(job_msg['data']['arguments']),
                 Status.WAITING,
                 key))

            if not rec:
                # no duplicate found, go on
                return 'initialized', None

            set_link(rec.id)

            if rec.result is not None and rec.status == Status.WORKFLOW:
                # the found duplicate returned a workflow
                if rec.link is not None:
                    # link is set, so result is fully realized
                    self.cur.execute(
                        'select * from "jobs" where "id" = ?',
                        (rec.link,))
                    rec = self.cur.fetchone()
                    assert rec is not None, "database integrity violation"
                    rec = JobEntry(*rec)

                else:
                    # link is not set, the result is still waited upon
                    assert rec.session == self.session, \
                        "database integrity violation"
                    self.attached[rec.id].append(key)
                    return 'attached', None

            if rec.result is not None:
                # result is found! return it
                result_value = self.registry.from_json(rec.result, deref=True)
                result = ResultMessage(
                    key, 'retrieved', result_value, None)
                return 'retrieved', result

            if rec.session == self.session:
                # still waiting for result, attach
                self.attached[rec.id].append(key)
                return 'attached', None

    def job_exists(self, prov):
        """Check if a job exists in the database."""
        with self.lock:
            self.cur.execute('select * from "jobs" where "prov" = ?;', (prov,))
            rec = self.cur.fetchone()
            return rec is not None

    def store_result_in_db(self, result, always_cache=True):
        """Store a result in the database."""
        job = self[result.key]

        def extend_dependent_links():
            with self.lock:
                new_workflow_id = id(get_workflow(result.value))
                self.links[new_workflow_id].extend(
                    self.links[id(job.workflow)])
                del self.links[id(job.workflow)]

        def store_result(status):
            result_value_msg = self.registry.to_json(result.value)
            with self.lock:
                self.cur.execute(
                    'update "jobs" set "result" = ?, '
                    '"status" = ? where "id" = ?;',
                    (result_value_msg, status, result.key))

        def acquire_links():
            with self.lock:
                linked_keys = tuple(self.links[id(job.workflow)])
                del self.links[id(job.workflow)]

                # update links for jobs up in the call-stack (parent workflows)
                n_questions = ','.join('?' * len(linked_keys))
                self.cur.execute(
                    'update "jobs" set "link" = ? where "id" in ({});'
                    .format(n_questions),
                    (result.key,) + linked_keys)

                # jobs that were attached to the parent workflow(s) will not
                # receive the current result automatically, so we need to force
                # feed them to the scheduler.
                attached_keys = ()
                for k in linked_keys:
                    attached_keys += tuple(self.attached[k])
                    del self.attached[k]

            return attached_keys

        # if the returned job is not set to be stored, but a parent job
        # is, we still need to store the result.
        if 'store' not in job.hints and not always_cache:
            if job.is_root_node and id(job.workflow) in self.links:
                if is_workflow(result.value):
                    extend_dependent_links()
                    return ()
                else:
                    store_result(Status.LINKEE)
                    return acquire_links()
            else:
                return ()

        # if the return value is a workflow, store the workflow, and add
        # links to this job, to be updated when the resolved result comes in
        if is_workflow(result.value):
            store_result(Status.WORKFLOW)
            with self.lock:
                self.links[id(get_workflow(result.value))].append(result.key)
            if job.is_root_node:
                extend_dependent_links()
            return ()

        store_result(Status.STORED)
        with self.lock:
            attached_keys = tuple(self.attached[result.key])
            del self.attached[result.key]

        if job.is_root_node:
            attached_keys += acquire_links()

        return attached_keys

    def add_time_stamp(self, db_id, name):
        """Add a timestamp to the database."""
        with self.lock:
            self.cur.execute(
                'insert into "timestamps" ("job", "what")'
                'values (?, ?);', (db_id, name))
