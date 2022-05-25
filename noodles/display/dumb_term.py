import logging

from .pretty_term import OutStream
from ..workflow import FunctionNode
from inspect import Parameter
import sys

logger = logging.getLogger("noodles")


def _format_arg_list(a, v):
    if len(a) == 0:
        if v:
            return "(\u2026)"
        else:
            return "()"

    s = "({0}{1})"
    for i in a[:-1]:
        s = s.format(str(i) if i != Parameter.empty else "\u2014", ", {0}{1}")

    if v:
        return s.format("\u2026", "")

    return s.format(str(a[-1]) if a[-1] != Parameter.empty else "\u2014", "")


class DumbDisplay:
    """Monochrome, dumb term display"""
    def __init__(self, error_filter=None):
        self.jobs = {}
        self.out = OutStream(sys.stdout)
        self.errors = []
        self.error_filter = error_filter
        self.messages = []

    def print_message(self, key, msg):
        if key in self.jobs:
            logger.info("{1:12} | {2}".format(
                    key, '['+msg.upper()+']', self.jobs[key]['name']))

    def add_job(self, key, name):
        self.jobs[key] = {'name': name}

    def error_handler(self, job, xcptn):
        self.errors.append((job, xcptn))

    def report(self):
        if len(self.errors) == 0:
            self.out << "[success]\n"

        else:
            self.out << "[ERROR!]\n\n"

            for job, e in self.errors:
                if 'display' in job.hints:
                    msg = job.hints['display'].format(
                        **job.bound_args.arguments)
                else:
                    msg = 'calling {} with {}'.format(
                        job.foo.__name__, dict(job.bound_args.arguments)
                    )

                logger.error(msg)
                err_msg = self.error_filter(e)
                if err_msg:
                    logger.error(err_msg)
                else:
                    logger.error(e)

    def __call__(self, msg):
        key, status, data, err = msg

        if isinstance(data, FunctionNode) and hasattr(data, 'hints'):
            job = data
            if job.hints and 'display' in job.hints:
                msg = job.hints['display'].format(**job.bound_args.arguments)
            else:
                msg = "{0} {1}".format(
                    job.foo.__name__,
                    _format_arg_list(job.bound_args.args, None))

            self.add_job(key, msg)

        if hasattr(self, status):
            getattr(self, status)(key, data, err)
        else:
            self.print_message(key, status)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self.wait()

        if exc_type:
            if exc_type is KeyboardInterrupt:
                self.out << "\n" << "User interrupt detected, abnormal exit.\n"
                return True

            logger.critical(
                "Internal error encountered. Contact the developers.",
                exc_info=exc_val,
            )
            return False

        self.report()

    def wait(self):
        self.q.wait()
