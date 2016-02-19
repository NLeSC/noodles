from .coroutines import coroutine_sink, Connection
# from .data_json import saucer, desaucer, node_to_jobject
from ..logger import log
from ..utility import object_name
from noodles import serial

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
        self.registry = serial.base
        self.jobs_scheme = 'local'
        self.files_scheme = 'local'
        self.location = None
        self.credential = None
        self.jobs_properties = None
        self.files_properties = None
        self.working_dir = os.getcwd()
        self.exec_command = None
        self.time_out = 5000  # 5 seconds
        self.prefix = sys.prefix

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
        self._x = keeper
        self._s = keeper.jobs.newScheduler(*config.scheduler_args)

    def submit(self, command, interactive=True):
        desc = xenon.jobs.JobDescription()
        if interactive:
            desc.setInteractive(True)
        desc.setExecutable(command[0])
        desc.setArguments(*command[1:])
        job = self._x.jobs.submitJob(self._s, desc)
        return XenonJob(self._x, job, desc)


def xenon_interactive_worker(config=None, init=None, finish=None):
    """Uses Xenon to run a single remote interactive worker.

    Jobs are read from stdin, and results written to stdout.

    :param config:
        The configuration for Xenon. This includes the kind
        of Xenon adaptor to use along with authentication credentials and the
        hostname of the machine.
    :type config: :py:class:`XenonConfig`

    :param init:
        Run this function on the remote worker once before doing jobs

    :param finish:
        Run this function after everything has finished, probably not
        very useful.
    """

    if config is None:
        config = XenonConfig()  # default config

    K = XenonKeeper(config.scheduler_args)

    cmd = config.exec_command if config.exec_command \
        else ['/bin/bash',
              config.working_dir + '/worker.sh',
              config.prefix,
              'online', '-name', K.name,
              '-registry', object_name(config.registry)]

    if init:
        cmd.append("-init")
    if finish:
        cmd.append("-finish")

    J = K.submit(cmd, interactive=True)

    status = J.wait_until_running(config.time_out)
    if not status.isRunning():
        raise RuntimeError("Could not get the job running")

    def read_stderr():
        for line in java_lines(J.streams.getStderr()):
            log.worker_stderr("Xe {0:X}".format(id(K)), line)

    K.stderr_thread = threading.Thread(target=read_stderr)
    K.stderr_thread.daemon = True
    K.stderr_thread.start()

    registry = config.registry()

    @coroutine_sink
    def send_job():
        out = jPrintStream(J.streams.getStdin())

        while True:
            key, ujob = yield
            out.println(put_job(registry, K.name, key, ujob))
            out.flush()

    def get_result():
        for line in java_lines(J.streams.getStdout()):
            key, status, result, err_msg = read_result(registry, line)
            yield (key, status, result, err_msg)

    if init is not None:
        send_job().send(("init", init()._workflow.root_node))
        key, status, result, err_msg = next(get_result())
        if key != "init" or not result:
            raise RuntimeError("The initializer function did not succeed on worker.")

    if finish is not None:
        send_job().send(("finish", finish()._workflow.root_node))

    return Connection(get_result, send_job)


# def xenon_batch_worker(poll_delay=1):
#     xenon.init()
#
#     x = xenon.Xenon()
#     jobs_api = x.jobs()
#
#     new_jobs = Queue()
#
#     @coroutine_sink
#     def send_job():
#         sched = jobs_api.newScheduler('ssh', 'localhost', None, None)
#
#         while True:
#             key, job = yield
#             pwd = 'noodles-{0}'.format(key.hex)
#             desc = xenon.jobs.JobDescription()
#             desc.setExecutable('python3.5')
#             desc.setStdout(os.getcwd() + '/' + pwd + '/out.json')
#
#             # submit a job
#             job = jobs_api.submitJob(sched, desc)
#             new_jobs.put((key, job))
#
#     def get_result():
#         jobs = {}
#
#         while True:
#             time.sleep(poll_delay)
#             for key, job in jobs.items():
#                 ...
#                 result = 42
#                 yield (key, result)
#
#             # put recently submitted jobs into the jobs-dict.
#             while not new_jobs.empty():
#                 key, job = new_jobs.get()
#                 jobs[key] = job
#                 new_jobs.task_done()
#
#     return Connection(get_result, send_job)
