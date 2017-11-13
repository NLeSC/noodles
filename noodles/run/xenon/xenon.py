# from ..logger import log
from ...utility import object_name
from noodles import serial
# from .hybrid import hybrid_threaded_worker

# import random
import uuid
import xenon
import os
import sys


class XenonConfig:
    """Configuration to the Xenon library.

    Xenon is a Java library that offers a uniform interface to execute jobs.
    These jobs may be run locally, over ssh ar against a queue manager like
    SLURM.

    [Documentation to Xenon can be found online](http://nlesc.github.io/Xenon)

    :param name:
        The quasi human readable name to give to this Xenon instance.
        This defaults to a generated UUID.

    :param jobs_scheme:
        The scheme by which to schedule jobs. Should be one of 'local', 'ssh',
        'slurm' etc. See the Xenon documentation.

    :param files_scheme:
        The scheme by which to transfer files. Should be 'local' or 'ssh'.
        See the Xenon documentation.

    :param location:
        A location. This can be the host of the 'ssh' or 'slurm' server.

    :param credential:
        To enter a server through ssh, we need to have some credentials.
        Preferably, you have a private/public key pair by which you can
        identify yourself. Otherwise, this would be a combination of
        username/password. This functions that can create a credential
        object can be found in Xenon.credentials in the Xenon documentation.

    :param jobs_properties:
        Configuration to the Xenon.jobs module.

    :param files_properties:
        Configuration to the Xenon.files module.
    """
    def __init__(self, *, name=None, jobs_scheme='local', files_scheme='local',
                 location=None, credential=None, jobs_properties=None,
                 files_properties=None):
        self.name = name or ("xenon-" + str(uuid.uuid4()))
        self.jobs_scheme = jobs_scheme
        self.files_scheme = files_scheme
        self.location = location
        self.credential = credential
        self.jobs_properties = jobs_properties
        self.files_properties = files_properties

    @property
    def scheduler_args(self):
        properties = xenon.conversions.dict_to_HashMap(self.jobs_properties)
        return (self.jobs_scheme, self.location,
                self.credential, properties)

    @property
    def filesystem_args(self):
        return (self.files_scheme, self.location,
                self.credential, self.files_properties)


class RemoteJobConfig(object):
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

    :param time_out:
        It may take a while before a job is actually running. This specifies
        the time to wait before giving up.
    """
    def __init__(self, *, name=None, working_dir=None, prefix=None,
                 exec_command=None, n_threads=1, registry=serial.base,
                 init=None, finish=None, verbose=False,
                 queue=None, time_out=5000):
        self.name = name or ("remote-" + str(uuid.uuid4()))
        self.working_dir = working_dir or os.getcwd()
        self.prefix = prefix or sys.prefix
        self.exec_command = exec_command
        self.n_threads = n_threads
        self.registry = registry
        self.init = init
        self.finish = finish
        self.verbose = verbose
        self.queue = queue
        self.time_out = time_out

    def command_line(self):
        cmd = ['/bin/bash',
               self.working_dir + '/worker.sh',
               self.prefix, 'online', '-name', self.name,
               '-registry', object_name(self.registry)]

        if self.init:
            cmd.extend(["-init", object_name(self.init)])
            # cmd.append("-init")

        if self.finish:
            cmd.extend(["-finish", object_name(self.finish)])
            # cmd.append("-finish")

        if self.verbose:
            cmd.append("-verbose")

        return cmd


class XenonJob:
    """Representative of a XenonJob.

    :param keeper:
        The XenonKeeper object.

    :param job:
        The internal job object.

    :param desc:
        The job description.
    """
    def __init__(self, keeper, job, desc):
        self.keeper = keeper
        self.job = job
        self.desc = desc

        if self.interactive:
            self.streams = self.get_streams()

    def wait_until_running(self, timeout):
        status = self.keeper.jobs.waitUntilRunning(
            self.job, timeout)
        return status

    def wait_until_done(self, timeout=0):
        status = self.keeper.jobs.waitUntilDone(
            self.job, timeout)
        return status

    def get_streams(self):
        return self.keeper.jobs.getStreams(self.job)

    @property
    def interactive(self):
        return self.job.isInteractive()


class XenonKeeper:
    is_initialized = False

    def __init__(self, log_level='ERROR'):
        if not XenonKeeper.is_initialized:
            xenon.init(log_level=log_level)  # noqa
            XenonKeeper.is_initialized = True

        self._x = xenon.Xenon()
        self.jobs = self._x.jobs()
        self.credentials = self._x.credentials()
        self._schedulers = {}

    def add_scheduler(self, config: XenonConfig):
        name = config.name
        self._schedulers[name] = XenonScheduler(self, config)
        return name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._x.close()


class XenonScheduler:
    def __init__(self, keeper, config):
        self.config = config
        self._x = keeper
        self._s = keeper.jobs.newScheduler(*config.scheduler_args)

    def submit(self, command, *, queue=None, interactive=True):
        desc = xenon.jobs.JobDescription()
        if interactive:
            desc.setInteractive(True)
        desc.setExecutable(command[0])
        desc.setArguments(command[1:])
        if queue:
            desc.setQueueName(queue)
        elif self.config.jobs_scheme == 'local':
            desc.setQueueName('multi')

        job = self._x.jobs.submitJob(self._s, desc)
        return XenonJob(self._x, job, desc)
