Co-routine brokers
==================

We use co-routines to communicate messages between different components
in the Noodles runtime. Co-routines can have input or output in two ways
*passive* and *active*. An example::

    def f_pulls(coroutine):
        for msg in coroutine:
            print(msg)

    def g_produces(lines):
        for l in lines:
            yield lines

    lines = ['aap', 'noot', 'mies']

    f_pulls(g_produces(lines))

This prints the words 'aap', 'noot' and 'mies'. This same program could be
written where the co-routine is the one recieving messages::

    def f_recieves():
        while True:
            msg = yield
            print(msg)

    def g_pushes(coroutine, lines):
        for l in lines:
            coroutine.send(l)

    sink = f_recieves()
    sink.send(None)  # the co-routine needs to be initialised
                     # alternatively, .next() does the same as .send(None)
    g_pushes(sink, lines)

The action of creating a co-routine and setting it to the first `yield` statement
can be performed by a little decorator::

    from functools import wraps

    def coroutine(f):
        @wraps(f)
        def g(*args, **kwargs):
            sink = f(*args, **kwargs)
            sink.send(None)
            return sink

        return g

So far so good. Now we add multi-threading to the mix.

Queues
------

Queues in python are thread-safe objects. We can define a new `IOQueue` object
that uses the python `Queue` to buffer and distribute messages over several threads::

    from queue import Queue

    class IOQueue(object):
        def __init__(self):
            self._q = Queue()

        def source(self):
            while True:
                msg = self._q.get()
                yield msg
                self._q.task_done()

        @coroutine
        def sink(self):
            while True:
                msg = yield
                self._q.put(msg)

        def wait(self):
            self.Q.join()

Note, that both ends of the queue are, as we call it, passive. We could make an active
source (it would become a normal function), taking a call-back as an argument. However,
we're designing the Noodles runtime so that it easy to interleave functionality. Moreover,
the `IOQueue` object is only concerned with the state of its own queue. The outside universe
is only represented by the `yield` statements, thus preserving the principle of encapsulation.

Scheduler
---------

The last constraint to the Noodles broker system is the layout of the `Scheduler` function,
arguably the most important function in Noodles, since it controls the execution of all
user code. The loop structure is as follows::

    class Scheduler:
        def __init__(self, worker):
            self.job_sink, self.result_source = worker()
            self.jobs = {}
            self.links = {}

        def initialise(self, workflow, target=None):
            self.links[id(workflow)] = target

            for node in workflow.nodes:
                if node.is_ready:
                    self.schedule(Job(workflow, node))

        def schedule(self, job):
            key = uuid()
            self.jobs[key] = job
            self.job_sink.send((key, job.function, job.args))

        def run(self, master):
            self.initialise(master)

            for key, result in self.result_source:
                if is_workflow(result):
                    initialise(result, target=key)
                    continue

                if self.jobs[key].is_root:
                    if job.workflow == master:
                        return result

                    key = self.links[id(job.workflow)]

                job = self.jobs[key]

                for node, arg in job.targets:
                    node.set_argument(arg, result)
                    if node.is_ready:
                        self.schedule(Job(job.workflow, node))

                del self.jobs[key]

What the scheduler doesn't know about, is *how* or *where* the jobs are
being executed. A simple worker that works with this scheduler is::

    def single_worker():
        jobs = IOQueue()

        def get_result(source):
            for key, function, args in source:
                yield (key, function(*args))

        return jobs.sink(), get_result(jobs.source())

Here we have the combination of an *active* scheduler and a *passive* worker.
Suppose we have an active worker implementation::

    def active_worker(job_source, result_sink):
        for key, function, args in job_source:
            result_sink.send((key, function(*args)))

Then we need passive glue to connect the worker with the scheduler. Moreover, to prevent deadlock the
scheduler and worker need to work in different threads. The glue is queue. The big question is: can we
come up with a semantic to connect the different parts and take care of threading active components
automatically?
