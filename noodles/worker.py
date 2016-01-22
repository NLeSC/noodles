"""
This is the Noodles executable worker module. This is usually run by the
scheduler to dispatch jobs remotely, using

.. code-block:: bash

    > python3.5 -m noodles.worker <args>...

There are several modes in which the worker generates results. For all
of these modes, the rule is **one object per line**.

:batch-mode: Give a single job as a JSON string on the command line. The
    result is printed to stdout, again as a JSON object.

    .. code-block:: bash

        > python3.5 -m noodles.worker -batch "{'job': ...}"

:online-mode: Recieve worker commands as JSON objects through stdin and
    send out results to stdout.

    .. code-block:: bash

        > python3.5 -m noodles.worker -online [-use <worker>]
"""

import argparse
import sys
import os
import uuid

import json
from .data_json import (desaucer, saucer, jobject_to_node, value_to_jobject)
from .run_common import run_job
from contextlib import redirect_stdout


def get_job(s):
    #    print(s, file=sys.stderr)
    obj = json.loads(s, object_hook=desaucer(deref=True))
    key = obj['key']
    node = jobject_to_node(obj['node'])
    return (key, node)


def put_result(host, key, result):
    return json.dumps(
        {'key': key, 'result': value_to_jobject(result)},
        default=saucer(host))


def run_batch_mode(args):
    print("Batch mode is not yet implemented")


def run_online_mode(args):
    if args.n == 1:
        finish = None

        # run the init function if it is given
        if args.init:
            line = sys.stdin.readline()
            key, job = get_job(line)
            if key != 'init':
                raise RuntimeError("Expected init function.")

            with redirect_stdout(sys.stderr):
                result = run_job(job)
            print(put_result(args.name, key, result), flush=True)

        if args.finish:
            line = sys.stdin.readline()
            key, job = get_job(line)
            if key != 'finish':
                raise RuntimeError("Expected finish function.")
            finish = job

        for line in sys.stdin:
            key, job = get_job(line)

            if args.jobdirs:
                # make a directory
                os.mkdir("noodles-{0}".format(key.hex))
                # enter it
                os.chdir("noodles-{0}".format(key.hex))

            if args.verbose:
                print("============\nraw json: ", line,
                      file=sys.stderr, flush=True)
                print("worker: ",
                      job.foo.__name__,
                      job.bound_args.args,
                      job.bound_args.kwargs,
                      file=sys.stderr, flush=True)

            with redirect_stdout(sys.stderr):
                result = run_job(job)

            if args.jobdirs:
                # parent directory
                os.chdir("..")

            print(put_result(args.name, key, result), flush=True)

        if finish:
            run_job(finish)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="{py} -m noodles.worker".format(
            py=os.path.basename(sys.executable)),

        description="This is the Noodles executable worker module. "
                    "This is usually run by the scheduler to dispatch "
                    "jobs remotely.")

    parser.add_argument(
        "-version", action="version", version="Noodles 0.1.0-alpha1")

    subparsers = parser.add_subparsers(
        title="Execution models",
        description="Noodles can execute jobs one at a time, or "
                    "streaming on stdin/stdout.")

    batch_parser = subparsers.add_parser(
        "batch", help="run a single job")
    batch_parser.add_argument(
        "-persist",
        help="keep going until a value, not another workflow, comes out.",
        default=False, action='store_true')
    batch_parser.set_defaults(func=run_batch_mode)

    online_parser = subparsers.add_parser(
        "online", help="stream jobs from standard input.")
    online_parser.add_argument(
        "-n", type=int,
        help="the number of threads.", default=1)
    online_parser.add_argument(
        "-verbose",
        help="output information to stderr for debugging",
        default=False, action='store_true')
    online_parser.add_argument(
        "-jobdirs",
        help="create a directory for each job to run in",
        default=False, action='store_true')
    online_parser.add_argument(
        "-name", type=str,
        help="worker identity",
        default="worker-" + str(uuid.uuid4()))
    online_parser.add_argument(
        "-init", help="an init function will be send before other jobs",
        default=False, action='store_true')
    online_parser.add_argument(
        "-finish", help="a finish function will be send before other jobs",
        default=False, action='store_true')

    online_parser.set_defaults(func=run_online_mode)

    args = parser.parse_args()
    args.func(args)
