from ...lib import (
    Queue, Connection, EndOfQueue, push, pull, pull_map, sink_map,
    thread_counter)

from ..messages import (
    JobMessage, ResultMessage, EndOfWork)

import threading
import sys
from collections import namedtuple

from .xenon import (Machine)
import grpc


def xenon_interactive_worker(
        machine, worker_config, input_queue=None, stderr_sink=None):
    """Uses Xenon to run a single remote interactive worker.

    Jobs are read from stdin, and results written to stdout.

    :param machine:
        Specification of the machine on which to run.
    :type machine: noodles.run.xenon.Machine

    :param worker_config:
        Job configuration. Specifies the command to be run remotely.
    :type worker_config: noodles.run.xenon.XenonJobConfig
    """
    if input_queue is None:
        input_queue = Queue()

    registry = worker_config.registry()

    @pull_map
    def serialise(obj):
        """Serialise incoming objects, yielding strings."""
        if isinstance(obj, JobMessage):
            print('serializing:', str(obj.node), file=sys.stderr)
        return (registry.to_json(obj, host='scheduler') + '\n').encode()

    @pull_map
    def echo(line):
        print('{} input: {}'.format(worker_config.name, line), file=sys.stderr)
        return line

    def do_iterate(source):
        for x in source():
            if x is EndOfQueue:
                yield EndOfWork
                return
            yield x

    job, output_stream = machine.scheduler.submit_interactive_job(
        worker_config.xenon_job_description,
        echo(lambda: serialise(lambda: do_iterate(input_queue.source))))

    @sink_map
    def echo_stderr(text):
        """Print lines."""
        for line in text.split('\n'):
            print("{}: {}".format(worker_config.name, line), file=sys.stderr)

    if stderr_sink is None:
        stderr_sink = echo_stderr()

    @pull
    def read_output(source):
        """Handle output from job, sending stderr data to given
        `stderr_sink`, passing on lines from stdout."""
        line_buffer = ""
        try:
            for chunk in source():
                if chunk.stdout:
                    lines = chunk.stdout.decode().splitlines(keepends=True)

                    if not lines:
                        continue

                    if lines[0][-1] == '\n':
                        yield line_buffer + lines[0]
                        line_buffer = ""
                    else:
                        line_buffer += lines[0]

                    if len(lines) == 1:
                        continue

                    yield from lines[1:-1]

                    if lines[-1][-1] == '\n':
                        yield lines[-1]
                    else:
                        line_buffer = lines[-1]

                if chunk.stderr:
                    for line in chunk.stderr.decode().split('\n'):
                        stripped_line = line.strip()
                        if stripped_line != '':
                            stderr_sink.send(stripped_line)

        except grpc.RpcError as e:
            return

    @pull_map
    def deserialise(line):
        result = registry.from_json(line, deref=False)
        return result

    return Connection(
        lambda: deserialise(lambda: read_output(lambda: output_stream)),
        input_queue.sink, aux=job)


class XenonInteractiveWorker(Connection):
    """Submits a new job to the specified queue. Starts a thread to
    read and forward stderr. Then acts as a `Connection` that goes
    online as soon as the submitted job is running.
    """
    def __init__(self, machine, worker_config):
        connection = xenon_interactive_worker(machine, worker_config)
        super(XenonInteractiveWorker, self).__init__(
                connection.source, connection.sink)

        self.worker_config = worker_config
        self.job = connection.aux
        self.machine = machine
        self.online = False

    def wait_until_running(self, callback=None):
        """Waits until the remote worker is running, then calls the callback.
        Usually, this method is passed to a different thread; the callback
        is then a function patching results through to the result queue."""
        status = self.machine.scheduler.wait_until_running(
                self.job, self.worker_config.time_out)

        if status.running:
            self.online = True
            if callback:
                callback(self)
        else:
            raise TimeoutError("Timeout while waiting for worker to run: " +
                               self.worker_config.name)

    def close(self):
        try:
            self.sink.send(EndOfQueue)
        except StopIteration:
            pass


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
    def __init__(self, machine: Machine):
        self.workers = {}
        self.machine = machine

        self.job_queue = Queue()
        self.result_queue = Queue()
        self.wlock = threading.Lock()
        self.plock = threading.Lock()
        self.count = thread_counter(self.result_queue.close)

        @push
        def dispatch_jobs():
            job_sink = self.job_queue.sink()

            while True:
                msg = yield

                for w in self.workers.values():
                    with w.lock:  # Worker lock ~~~~~~~~~~~~~~~~~~~~~
                        if len(w.jobs) < w.max:
                            w.sink.send(msg)
                            w.jobs.append(msg.key)
                            break
                    # lock end ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                else:
                    job_sink.send(msg)

        super(DynamicPool, self).__init__(
            self.result_queue.source, dispatch_jobs)

    def close_all(self):
        for w in self.workers.values():
            try:
                w.sink.send(EndOfQueue)
            except StopIteration:
                pass

    def add_xenon_worker(self, worker_config):
        """Adds a worker to the pool; sets gears in motion."""
        c = XenonInteractiveWorker(self.machine, worker_config)
        w = RemoteWorker(
            worker_config.name, threading.Lock(),
            worker_config.n_threads, [], *c.setup())

        with self.wlock:
            self.workers[worker_config.name] = w

        def populate(job_source):
            """Populate the worker with jobs, if jobs are available."""
            with w.lock, self.plock:  # Worker lock ~~~~~~~~~~~~~~~~~~
                while len(w.jobs) < w.max and not self.job_queue.empty():
                    msg = next(job_source)
                    w.sink.send(msg)

                    if msg is not EndOfQueue:
                        key, job = msg
                        w.jobs.append(key)
                    else:
                        break
            # lock end ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        def activate(_):
            """Activate the worker."""
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
        t = threading.Thread(
            target=self.count(c.wait_until_running), args=(activate,),
            daemon=True)
        t.start()
