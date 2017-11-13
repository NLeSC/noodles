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
import uuid
from contextlib import redirect_stdout

import os
from .utility import (look_up)

try:
    import msgpack
    has_msgpack = True
except ImportError:
    has_msgpack = False

from .run.worker import (
    run_job)

from .run.messages import (
    JobMessage)

from .run.remote.io import (
    MsgPackObjectReader, MsgPackObjectWriter,
    JSONObjectReader, JSONObjectWriter)


def run_batch_mode(args):
    print("Batch mode is not yet implemented")


def run_online_mode(args):
    if args.n == 1:
        registry = look_up(args.registry)()
        finish = None

        if args.msgpack:
            newin = os.fdopen(sys.stdin.fileno(), 'rb', buffering=0)
            input_stream = MsgPackObjectReader(
                registry, newin, deref=True)
            output_stream = MsgPackObjectWriter(
                registry, sys.stdout.buffer, host=args.name)
        else:
            input_stream = JSONObjectReader(
                registry, sys.stdin, deref=True)
            output_stream = JSONObjectWriter(
                registry, sys.stdout, host=args.name)

        # run the init function if it is given
        if args.init:
            with redirect_stdout(sys.stderr):
                look_up(args.init)()

        if args.finish:
            finish = look_up(args.finish)

        for msg in input_stream:
            if isinstance(msg, JobMessage):
                key, job = msg
            elif isinstance(msg, tuple):
                key, job = msg
            else:
                continue

            if args.jobdirs:
                # make a directory
                os.mkdir("noodles-{0}".format(key.hex))
                # enter it
                os.chdir("noodles-{0}".format(key.hex))

            if args.verbose:
                print("worker: ",
                      job.foo.__name__,
                      job.bound_args.args,
                      job.bound_args.kwargs,
                      file=sys.stderr, flush=True)

            with redirect_stdout(sys.stderr):
                result = run_job(key, job)

            if args.verbose:
                print("result: ", result, file=sys.stderr, flush=True)

            if args.jobdirs:
                # parent directory
                os.chdir("..")

            output_stream.send(result)

        if finish:
            finish()


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
        "-registry", type=str,
        help="the serial registry")
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
        "-msgpack",
        help="use MessagePack for serialisation.",
        default=False, action='store_true')
    online_parser.add_argument(
        "-name", type=str,
        help="worker identity",
        default="worker-" + str(uuid.uuid4()))
    online_parser.add_argument(
        "-init", type=str,
        help="an init function will be send before other jobs",
        default=None)
    online_parser.add_argument(
        "-finish", type=str,
        help="a finish function will be send before other jobs",
        default=None)

    online_parser.set_defaults(func=run_online_mode)

    args = parser.parse_args()
    args.func(args)
