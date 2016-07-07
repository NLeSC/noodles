from .connection import Connection
from .coroutine import coroutine
from .queue import Queue
# from ..logger import log
from ..utility import object_name
from noodles import serial
# from .hybrid import hybrid_threaded_worker
from .scheduler import Scheduler
from ..workflow import get_workflow

from copy import copy

# import random
import uuid
import xenon
import os
import sys
import threading
import jpype

# from contextlib import redirect_stderr
# xenon_log = open('xenon_log.txt', 'w')
# with redirect_stderr(xenon_log):
xenon.init()  # noqa

from xenon import java


def read_result(registry, s):
    obj = registry.from_json(s)
    status = obj['status']
    key = obj['key']
    try:
        key = uuid.UUID(key)
    except ValueError:
        pass

    return key, status, obj['result'], obj['err_msg']


def put_job(registry, host, key, job):
    obj = {'key': key if isinstance(key, str) else key.hex,
           'node': job}
    return registry.to_json(obj, host=host)


jPrintStream = java.io.PrintStream
jBufferedReader = java.io.BufferedReader
jInputStreamReader = java.io.InputStreamReader
jScanner = java.util.Scanner


class XenonConfig:
    """Configuration to the Xenon library.

    Xenon is a Java library that offers a uniform interface to execute jobs.
    These jobs may be run locally, over ssh ar against a queue manager like
    SLURM.

    [Documentation to Xenon can be found online](http://nlesc.github.io/xenon)

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
                 exec_command=None, registry=serial.base,
                 init=None, finish=None, verbose=False,
                 queue=None, time_out=5000):
        self.name = name or ("remote-" + str(uuid.uuid4()))
        self.working_dir = working_dir or os.getcwd()
        self.prefix = prefix or sys.prefix
        self.exec_command = exec_command
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
            cmd.append("-init")

        if self.finish:
            cmd.append("-finish")

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
    def __init__(self):
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


def xenon_interactive_worker(XeS: XenonScheduler, job_config):
    """Uses Xenon to run a single remote interactive worker.

    Jobs are read from stdin, and results written to stdout.

    :param XeS:
        The :py:class:`XenonScheduler` object that allows us to schedule the
        new worker.
    :type Xe: XenonScheduler

    :param job_config:
        Job configuration. Specifies the command to be run remotely.
    """
    cmd = job_config.command_line()
    J = XeS.submit(cmd, interactive=True)

    # status = J.wait_until_running(job_config.time_out)
    # if not status.isRunning():
    #     raise RuntimeError("Could not get the job running")
    # else:
    #     print(job_config.name + " is now running.",
    # file=sys.stderr, flush=True)

    # print(job_config.name + " is now running.", file=sys.stderr, flush=True)

    def read_stderr():
        jpype.attachThreadToJVM()
        for line in xenon.conversions.read_lines(J.streams.getStderr()):
            print(job_config.name + ": " + line, file=sys.stderr, flush=True)

    J.stderr_thread = threading.Thread(target=read_stderr)
    J.stderr_thread.daemon = True
    J.stderr_thread.start()

    registry = job_config.registry()

    @coroutine
    def send_job():
        out = jPrintStream(J.streams.getStdin())

        while True:
            key, ujob = yield
            out.println(put_job(registry, 'scheduler', key, ujob))
            out.flush()

    def get_result():
        """ Returns a result tuple: key, status, result, err_msg """
        for line in xenon.conversions.read_lines(J.streams.getStdout()):
            yield read_result(registry, line)

    if job_config.init is not None:
        send_job().send(("init", job_config.init()._workflow.root_node))
        key, status, result, err_msg = next(get_result())
        if key != "init" or not result:
            raise RuntimeError("The initializer function did not succeed on "
                               "worker.")

    if job_config.finish is not None:
        send_job().send(("finish", job_config.finish()._workflow.root_node))

    return Connection(get_result, send_job)


def buffered_dispatcher(workers):
    jobs = Queue()
    results = Queue()

    def dispatcher(source, sink):
        jpype.attachThreadToJVM()
        result_sink = results.sink()

        for job in jobs.source():
            sink.send(job)
            result_sink.send(next(source))

    for w in workers.values():
        t = threading.Thread(
            target=dispatcher,
            args=w.setup())
        t.daemon = True
        t.start()

    return Connection(results.source, jobs.sink)


def run_xenon(Xe, n_processes, xenon_config, job_config, wf, deref=False):
    """Run the workflow using a number of online Xenon workers.

    :param Xe:
        The XenonKeeper instance.

    :param wf:
        The workflow.
    :type wf: `Workflow` or `PromisedObject`

    :param n_processes:
        Number of processes to start.

    :param xenon_config:
        The :py:class:`XenonConfig` object that gives tells us how to use
        Xenon.

    :param job_config:
        The :py:class:`RemoteJobConfig` object that specifies the command to
        run remotely for each worker.

    :param deref:
        Set this to True to pass the result through one more encoding and
        decoding step with object derefencing turned on.
    :type deref: bool

    :returns: the result of evaluating the workflow
    :rtype: any
    """
    XeS = XenonScheduler(Xe, xenon_config)

    workers = {}
    for i in range(n_processes):
        cfg = copy(job_config)
        cfg.name = 'remote-{0:02}'.format(i)
        new_worker = xenon_interactive_worker(XeS, cfg)
        workers[cfg.name] = new_worker

    master_worker = buffered_dispatcher(workers)
    result = Scheduler().run(master_worker, get_workflow(wf))

    if deref:
        return job_config.registry().dereference(result, host='localhost')
    else:
        return result
