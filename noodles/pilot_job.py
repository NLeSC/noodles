"""
This is the Noodles executable worker module. This is usually run by the
scheduler to dispatch jobs remotely, using

.. code-block:: bash

    > python3 -m noodles.pilot_job <args>...

Recieve worker commands as JSON objects through stdin and send out results to
stdout.

    .. code-block:: bash

        > python3 -m noodles.worker -online [-use <worker>]
"""

import argparse
import sys
import uuid
from contextlib import redirect_stdout

import time
import os

from noodles import __version__
from .lib import (look_up)
from .run.messages import (EndOfWork)

from .run.worker import (
    run_job)

from .run.messages import (
    JobMessage)

from .run.remote.io import (JSONObjectReader, JSONObjectWriter)


def run_online_mode(args):
    """Run jobs.

    :param args: arguments resulting from program ArgumentParser.
    :return: None

    This reads messages containing job descriptions from standard input,
    and writes messages to standard output containing the result.

    Messages can be encoded as either JSON or MessagePack.
    """
    print("\033[47;30m Netherlands\033[48;2;0;174;239;37m▌"
          "\033[38;2;255;255;255me\u20d2Science\u20d2\033[37m▐"
          "\033[47;30mcenter \033[m Noodles worker", file=sys.stderr)

    if args.n == 1:
        registry = look_up(args.registry)()
        finish = None

        input_stream = JSONObjectReader(
            registry, sys.stdin, deref=True)
        output_stream = JSONObjectWriter(
            registry, sys.stdout, host=args.name)
        sys.stdout.flush()

        # run the init function if it is given
        if args.init:
            with redirect_stdout(sys.stderr):
                look_up(args.init)()

        if args.finish:
            finish = look_up(args.finish)

        for msg in input_stream:
            if isinstance(msg, JobMessage):
                key, job = msg
            elif msg is EndOfWork:
                print("received EndOfWork, bye", file=sys.stderr)
                sys.exit(0)
            elif isinstance(msg, tuple):
                key, job = msg
            elif msg is None:
                continue
            else:
                raise RuntimeError("Unknown message received: {}".format(msg))

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
                print("result: ", result.value, file=sys.stderr, flush=True)

            if args.jobdirs:
                # parent directory
                os.chdir("..")

            output_stream.send(result)

        if finish:
            finish()

        time.sleep(0.1)
        sys.stdout.flush()
        sys.stderr.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="{py} -m noodles.worker".format(
            py=os.path.basename(sys.executable)),

        description="This is the Noodles executable worker module. "
                    "This is usually run by the scheduler to dispatch "
                    "jobs remotely.")

    parser.add_argument(
        "-version", action="version", version="Noodles {}".format(__version__))
    parser.add_argument(
        "-registry", type=str,
        help="the serial registry")
    parser.add_argument(
        "-n", type=int,
        help="the number of threads.", default=1)
    parser.add_argument(
        "-verbose",
        help="output information to stderr for debugging",
        default=False, action='store_true')
    parser.add_argument(
        "-jobdirs",
        help="create a directory for each job to run in",
        default=False, action='store_true')
    parser.add_argument(
        "-name", type=str,
        help="worker identity",
        default="worker-" + str(uuid.uuid4()))
    parser.add_argument(
        "-init", type=str,
        help="an init function will be send before other jobs",
        default=None)
    parser.add_argument(
        "-finish", type=str,
        help="a finish function will be send before other jobs",
        default=None)

    run_online_mode(parser.parse_args())
