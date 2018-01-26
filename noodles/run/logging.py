from ..lib import (EndOfQueue)
from .messages import (JobMessage, ResultMessage)
import logging


def make_logger(name, stream_type, jobs):
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
