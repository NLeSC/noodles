"""
Provides logging facilities that can be inserted at any place in a system
of streams.
"""

import logging

from ..lib import (EndOfQueue)
from ..workflow import (is_workflow)
from .messages import (JobMessage, ResultMessage)


def _sugar(s):
    """Shorten strings that are too long for decency."""
    # s = s.replace("{", "{{").replace("}", "}}")
    if len(s) > 50:
        return s[:20] + " ... " + s[-20:]
    else:
        return s


def make_logger(name, stream_type, jobs):
    """Create a logger component.

    :param name: name of logger child, i.e. logger will be named
        `noodles.<name>`.
    :type name: str
    :param stream_type: type of the stream that this logger will
        be inserted into, should be |pull_map| or |push_map|.
    :type stream_type: function
    :param jobs: job-keeper instance.
    :type jobs: dict, |JobKeeper| or |JobDB|.

    :return: a stream.

    The resulting stream receives messages and sends them on after
    sending an INFO message to the logger. In the case of a |JobMessage|
    or |ResultMessage| a meaningful message is composed otherwise the
    string representation of the object is passed."""
    logger = logging.getLogger('noodles').getChild(name)
    # logger.setLevel(logging.DEBUG)

    @stream_type
    def log_message(message):
        if message is EndOfQueue:
            logger.info("-end-of-queue-")

        elif isinstance(message, JobMessage):
            logger.info(
                "job    %10s: %s", message.key, message.node)

        elif isinstance(message, ResultMessage):
            job = jobs[message.key]
            if is_workflow(message.value):
                logger.info(
                    "result %10s [%s]: %s -> workflow %x", message.key,
                    job.node, message.status, id(message.value))
            else:
                value_string = repr(message.value)
                logger.info(
                    "result %10s [%s]: %s -> %s", message.key, job.node,
                    message.status, _sugar(value_string))

        else:
            logger.info(
                "unknown message: %s", message)

        return message

    return log_message
