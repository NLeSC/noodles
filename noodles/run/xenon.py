from .coroutines import coroutine_sink, Connection
# from .data_json import saucer, desaucer, node_to_jobject
from ..logger import log
from ..utility import object_name
from noodles import serial
from .hybrid import hybrid_threaded_worker
from .scheduler import Scheduler
from ..workflow import get_workflow

from copy import copy

import random
import uuid
import xenon
import os
import sys
import threading

# from contextlib import redirect_stderr
# xenon_log = open('xenon_log.txt', 'w')
# with redirect_stderr(xenon_log):
xenon.init()  # noqa

from jnius import autoclass


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


jPrintStream = autoclass('java.io.PrintStream')
jBufferedReader = autoclass('java.io.BufferedReader')
jInputStreamReader = autoclass('java.io.InputStreamReader')
jScanner = autoclass('java.util.Scanner')


def java_lines(inp):
    reader = jScanner(inp)

    while True:
        line = reader.nextLine()
        yield line

HashMap = autoclass('java.util.HashMap')


def dict2HashMap(d):
    if d is None:
        return None

    m = HashMap()
    for k, v in d.items():
        m.put(k, v)
    return m


class XenonConfig:
    def __init__(self, **kwargs):
        self.name = "xenon-" + str(uuid.uuid4())
        self.jobs_scheme = 'local'
        self.files_scheme = 'local'
        self.location = None
        self.credential = None
        self.jobs_properties = None
        self.files_properties = None

        for key, value in kwargs.items():
            if key in dir(self):
                setattr(self, key, value)
            else:
                raise ValueError("Keyword `{}' not part of Xenon config.".format(key))

    @property
    def scheduler_args(self):
        properties = dict2HashMap(self.jobs_properties)
        return (self.jobs_scheme, self.location,
                self.credential, properties)

    @property
    def filesystem_args(self):
        return (self.files_scheme, self.location,
                self.credential, self.files_properties)


class RemoteJobConfig(object):
    def __init__(self, **kwargs):
        self.name = "remote-" + str(uuid.uuid4())
        self.working_dir = os.getcwd()
        self.prefix = sys.prefix
        self.exec_command = None
        self.registry = serial.base
        self.init = None
        self.finish = None
        self.verbose = False
        self.queue = None
        self.time_out = 5000  # 5 seconds

        for key, value in kwargs.items():
            if key in dir(self):
                setattr(self, key, value)
            else:
                raise ValueError("Keyword `{}' not part of Remote Job config.".format(key))

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
        desc.setArguments(*command[1:])
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
    #     print(job_config.name + " is now running.", file=sys.stderr, flush=True)

    print(job_config.name + " is now running.", file=sys.stderr, flush=True)
    def read_stderr():
        for line in java_lines(J.streams.getStderr()):
            print(job_config.name + ": " + line, file=sys.stderr, flush=True)

    J.stderr_thread = threading.Thread(target=read_stderr)
    J.stderr_thread.daemon = True
    J.stderr_thread.start()

    registry = job_config.registry()

    @coroutine_sink
    def send_job():
        out = jPrintStream(J.streams.getStdin())

        while True:
            key, ujob = yield
            out.println(put_job(registry, 'scheduler', key, ujob))
            out.flush()

    def get_result():
        for line in java_lines(J.streams.getStdout()):
            key, status, result, err_msg = read_result(registry, line)
            yield (key, status, result, err_msg)

    if job_config.init is not None:
        send_job().send(("init", job_config.init()._workflow.root_node))
        key, status, result, err_msg = next(get_result())
        if key != "init" or not result:
            raise RuntimeError("The initializer function did not succeed on worker.")

    if job_config.finish is not None:
        send_job().send(("finish", job_config.finish()._workflow.root_node))

    return Connection(get_result, send_job)


def buffered_dispatcher(workers):
    jobs = IOQueue()
    results = IOQueue()

    def dispatcher(source, sink):
        result_sink = results.sink()

        for job in jobs.source():
            sink.send(job)
            result_sink.send(source.next())

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
        The :py:class:`XenonConfig` object that gives tells us how to use Xenon.

    :param job_config:
        The :py:class:`RemoteJobConfig` object that specifies the command to run
        remotely for each worker.

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
        cfg = copy.copy(job_config)
        cfg.name = 'remote-{0:02}'.format(i)
        new_worker = xenon_interactive_worker(XeS, cfg)
        workers[new_worker.name] = new_worker

    master_worker = buffered_dispatcher(workers)
    result = Scheduler().run(master_worker, get_workflow(wf))

    if deref:
        return job_config.registry().dereference(result, host='localhost')
    else:
        return result


