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
from noodles.run.worker import run_job
from .utility import (look_up)

try:
    import msgpack
    has_msgpack = True
except ImportError:
    has_msgpack = False


def get_job(msg):
    return msg['key'], msg['node']


def get_job_json(registry, s):
    obj = registry.from_json(s, deref=True)
    return obj['key'], obj['node']


def put_result_msgpack(registry, host, key, status, result, err_msg):
    return registry.to_msgpack({
        'key': key,
        'status': status,
        'result': result,
        'err_msg': err_msg
    }, host=host)


def put_result_json(registry, host, key, status, result, err_msg):
    return registry.to_json({
        'key': key,
        'status': status,
        'result': result,
        'err_msg': err_msg
    }, host=host)


def run_batch_mode(args):
    print("Batch mode is not yet implemented")


def run_online_mode(args):
    if args.n == 1:
        registry = look_up(args.registry)()
        finish = None

        if args.msgpack:
            messages = msgpack.Unpacker(sys.stdin.buffer)
        else:
            def msg_stream():
                for line in sys.stdin:
                    yield registry.from_json(line, deref=True)

            messages = msg_stream()

        # run the init function if it is given
        if args.init:
            # line = sys.stdin.readline()
            key, job = get_job(next(messages))
            if key != 'init':
                raise RuntimeError("Expected init function.")

            with redirect_stdout(sys.stderr):
                result = run_job(key, job)

            if args.msgpack:
                sys.stdout.buffer.write(put_result_msgpack(
                    registry, args.name, *result))
                sys.stdout.flush()
            else:
                print(put_result_json(registry, args.name, *result),
                      flush=True)

        if args.finish:
            # line = sys.stdin.readline()
            key, job = get_job(next(messages))
            if key != 'finish':
                raise RuntimeError("Expected finish function.")
            finish = job

        for msg in messages:
            key, job = get_job(msg)

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
                print("json: ", put_result_json(
                    registry, args.name, key,
                    'success', result, None), file=sys.stderr, flush=True)

            if args.jobdirs:
                # parent directory
                os.chdir("..")

            if args.msgpack:
                sys.stdout.buffer.write(put_result_msgpack(
                    registry, args.name, *result))
                sys.stdout.flush()
            else:
                print(put_result_json(registry, args.name, *result),
                      flush=True)

        if finish:
            run_job(0, finish)


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
        "-init", help="an init function will be send before other jobs",
        default=False, action='store_true')
    online_parser.add_argument(
        "-finish", help="a finish function will be send before other jobs",
        default=False, action='store_true')

    online_parser.set_defaults(func=run_online_mode)

    args = parser.parse_args()
    args.func(args)
