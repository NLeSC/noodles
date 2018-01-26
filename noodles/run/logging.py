from ..lib import (EndOfQueue)
from .messages import (JobMessage, ResultMessage)
import logging


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

    @stream_type
    def log_message(message):
        if message is EndOfQueue:
            logger.info("-end-of-queue-")

        elif isinstance(message, JobMessage):
            logger.info(
                "job %s: %s", message.key, message.node)

        elif isinstance(message, ResultMessage):
            job = jobs[message.key]
            logger.info(
                "result %s [%s]: %s %s", message.key, job.node,
                message.status, message.value)

        else:
            logger.info(
                "unknown message: %s", message)

        return message

    return log_message
