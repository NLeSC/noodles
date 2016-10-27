"""
Messages to facilitate communication between scheduler and remote workers.
There are currently three types of messages:

    * ``JobMessage``, sending a job to a worker.
    * ``ResultMessage``, a worker returning a result.
    * ``PilotMessage``, extra communication back and forth, status updates,
    performance information, but also stopping a worker in a nice way.
"""

from ..serial import Reasonable


class JobMessage(Reasonable):
    def __init__(self, key, node):
        self.key = key
        self.node = node

    def __iter__(self):
        return iter((self.key, self.node))
        
        
class ResultMessage(Reasonable):
    def __init__(self, key, status, value, msg):
        self.key = key
        self.status = status
        self.value = value
        self.msg = msg

    def __iter__(self):
        return iter((self.key, self.status, self.value, self.msg))


class PilotMessage(Reasonable):
    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.__dict__.update(kwargs)

