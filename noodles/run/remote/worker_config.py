from pathlib import Path
import uuid
import os
import sys

from noodles import serial
from ...lib import object_name


class WorkerConfig(object):
    """Configuration for a single remote Job.

    :param name:
        A quasi human recognizable name for this job. This will default to
        'remote-xxxxxx' where 'xxxxx' is some UUID.

    :param working_dir:
        The work directory where the job runs. Defaults to the current working
        directory.

    :param prefix:
        The path prefix of the Python system we're running on. This defaults to
        `sys.prefix`. If we are in a VirtualEnv, this means that the spawned
        job will run in the same VirtualEnv.

    :param exec_command:
        The command that is being executed. This defaults to `worker.sh` which
        should be located in the `working_dir`. This default script initialises
        the VirtualEnv en starts Python with `-m noodles.worker`, acting as a
        pilot job.

    :param init:
        You may specify a function that needs to be run before any jobs are
        being executed. There exist frameworks in the wild, which won't
        function otherwise.

    :param finish:
        This function may do some clean up, after all jobs have been done.

    :param verbose:
        Be verbose about what we're doing. This is for debugging purposes only.
    """
    def __init__(self, *, name=None, working_dir=None, prefix=None,
                 exec_command=None, n_threads=1, registry=serial.base,
                 init=None, finish=None, verbose=False):
        self.name = name or ("remote-" + str(uuid.uuid4()))
        self.working_dir = working_dir or os.getcwd()
        self.prefix = prefix or Path(sys.prefix)
        self.exec_command = exec_command
        self.n_threads = n_threads
        self.registry = registry
        self.init = init
        self.finish = finish
        self.verbose = verbose

    def command_line(self):
        executable = self.prefix / 'bin' / 'python'

        arguments = [
            '-m', 'noodles.pilot_job',
            '-name', self.name,
            '-registry', object_name(self.registry)]

        if self.init:
            arguments.extend(["-init", object_name(self.init)])

        if self.finish:
            arguments.extend(["-finish", object_name(self.finish)])

        if self.verbose:
            arguments.append("-verbose")

        return executable, arguments
