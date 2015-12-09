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
from .data_json import (json_desauce, json_sauce, jobject_to_node)
from .run_common import run_job
from .decorator import unwrap


def get_job(s):
    obj = json.loads(s, object_hook=json_desauce)
    key = uuid.UUID(obj['key'])
    node = jobject_to_node(obj['node'])
    return (key, node)


def put_result(key, result):
    return json.dumps(
        {'key': key.hex, 'result': result},
        default=json_sauce)


def run_batch_mode(args):
    print("Batch mode is not yet implemented")


def run_online_mode(args):
    if args.n == 1:
        for line in sys.stdin:
            key, job = get_job(line)
            result = run_job(job)
            print(put_result(key, result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="{py} -m noodles.worker".format(
            py=os.path.basename(sys.executable)),

        description="This is the Noodles executable worker module. "
                    "This is usually run by the scheduler to dispatch "
                    "jobs remotely.")

    parser.add_argument(
        "--version", action="version", version="Noodles 0.1.0-alpha1")

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
    online_parser.set_defaults(func=run_online_mode)

    args = parser.parse_args()
    args.func(args)
