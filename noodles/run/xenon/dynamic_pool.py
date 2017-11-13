from ..queue import Queue
from ..connection import Connection
from ..haploid import (push)

from ..messages import (
    ResultMessage)

from ..remote.io import (
    JSONObjectWriter, JSONObjectReader)

import xenon
import jpype

import threading
import sys
from collections import namedtuple

from .xenon import (XenonKeeper, XenonConfig, XenonScheduler)


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
    queue = job_config.queue
    J = XeS.submit(cmd, interactive=True, queue=queue)

    def read_stderr():
        jpype.attachThreadToJVM()
        for line in xenon.conversions.read_lines(J.streams.getStderr()):
            print(job_config.name + ": " + line, file=sys.stderr, flush=True)

    J.stderr_thread = threading.Thread(target=read_stderr)
    J.stderr_thread.daemon = True
    J.stderr_thread.start()

    registry = job_config.registry()

    @push
    def send_job():
        output_stream = xenon.conversions.OutputStream(J.streams.getStdin())
        yield from JSONObjectWriter(registry, output_stream, host="scheduler")

    # @pull
    def get_result():
        input_stream = xenon.conversions.InputStream(J.streams.getStdout())
        yield from JSONObjectReader(registry, input_stream)

    return Connection(get_result, send_job, aux=J)


class XenonInteractiveWorker(Connection):
    """Submits a new job to the specified queue. Starts a thread to
    read and forward stderr. Then acts as a `Connection` that goes
    online as soon as the submitted job is running.
    """
    def __init__(self, sched, job_config):
        connection = xenon_interactive_worker(sched, job_config)
        super(XenonInteractiveWorker, self).__init__(*connection)

        self.job_config = job_config
        self.job = connection.aux
        self.online = False

    def init_worker(self):
        """Sends the `init` and `finish` jobs to the worker if this is needed.
        This part will be called first, after a remote worker goes online."""
        pass
        # print("Initializing worker: ", end='', flush=True)
        # if self.job_config.init is not None:
        #     print("[init] ", end='', flush=True)
        #     self.sink().send(
        #         ("init", self.job_config.init()._workflow.root_node))
        #     key, status, result, err_msg = next(self.source())
        #     if key != "init" or not result:
        #         raise RuntimeError(
        #             "The initializer function did not succeed on worker.")
        #
        # if self.job_config.finish is not None:
        #     self.sink().send(
        #         ("finish", self.job_config.finish()._workflow.root_node))
        # print("[done]", flush=True)

    def wait_until_running(self, callback=None):
        """Waits until the remote worker is running, then calls the callback.
        Usually, this method is passed to a different thread; the callback
        is then a function patching results through to the result queue."""
        jpype.attachThreadToJVM()
        status = self.job.wait_until_running(self.job_config.time_out)
        if status.isRunning():
            self.online = True
            self.init_worker()
            if callback:
                callback(self)
        else:
            raise TimeoutError("Timeout while waiting for worker to run: " +
                               self.job_config.name)


RemoteWorker = namedtuple('RemoteWorker', [
    'name', 'lock', 'max', 'jobs', 'source', 'sink'])


class DynamicPool(Connection):
    """Keeps a pool of Xenon workers. At each instant, when a job is sent to
    the recieving coroutine associated with this `Connection`, we look if
    there is a worker idle and send it there. If no worker is idle, the job
    is pushed on the queue. Whenever a worker returns a result, we replennish
    its list of jobs from the queue. In this way we can supply a variable
    amount of workers, each with their own preferred amount of jobs. As of
    yet, we have no mechanism to distribute the jobs between workers in any
    way more knowledgable than that."""
    def __init__(self, Xe: XenonKeeper, xenon_config: XenonConfig):
        self.workers = {}
        self.XeS = XenonScheduler(Xe, xenon_config)
        self.job_queue = Queue()
        self.result_queue = Queue()
        self.lock = threading.Lock()

        @push
        def dispatch_jobs():
            job_sink = self.job_queue.sink()

            while True:
                key, job = yield

                for w in self.workers.values():
                    with w.lock:  # Worker lock ~~~~~~~~~~~~~~~~~~~~~
                        if len(w.jobs) < w.max:
                            w.sink.send((key, job))
                            w.jobs.append(key)
                            break
                    # lock end ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                else:
                    job_sink.send((key, job))

        super(DynamicPool, self).__init__(
            self.result_queue.source, dispatch_jobs)

    def add_xenon_worker(self, job_config):
        """Adds a worker to the pool; sets gears in motion."""
        c = XenonInteractiveWorker(self.XeS, job_config)
        w = RemoteWorker(
            job_config.name, threading.Lock(),
            job_config.n_threads, [],
            *c.setup())

        with self.lock:
            self.workers[job_config.name] = w

        def populate(job_source):
            """Populate the worker with jobs, if jobs are available."""
            with w.lock, self.lock:  # Worker lock ~~~~~~~~~~~~~~~~~~
                while len(w.jobs) < w.max and not self.job_queue.empty():
                    key, job = next(job_source)
                    w.sink.send((key, job))
                    w.jobs.append(key)
            # lock end ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        def activate(_):
            """Activate the worker."""
            jpype.attachThreadToJVM()

            job_source = self.job_queue.source()
            populate(job_source)

            sink = self.result_queue.sink()

            for result in w.source:
                sink.send(result)

                # do bookkeeping and submit a new job to the worker
                with w.lock:  # Worker lock ~~~~~~~~~~~~~~~~~~~~~
                    w.jobs.remove(result.key)
                populate(job_source)
                # lock end ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            for key in w.jobs:
                sink.send(ResultMessage(
                    key, 'aborted', None, 'connection to remote worker lost.'))

        # Start the `activate` function when the worker goes online.
        threading.Thread(
            target=c.wait_until_running, args=(activate,),
            daemon=True).start()
