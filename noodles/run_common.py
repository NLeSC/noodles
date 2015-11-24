from .datamodel import *
from queue import Queue
import uuid
from functools import wraps

def run_job(node):
    return node.foo(*node.bound_args.args, **node.bound_args.kwargs)

def get_hints(node):
    return node.hints

Job = namedtuple('Job', ['workflow', 'node'])

DynamicLink = namedtuple('DynamicLink', ['source', 'target', 'node'])

def coroutine_sink(f):
    @wraps(f)
    def g(*args, **kwargs):
        sink = f(*args, **kwargs)
        sink.send(None)
        return sink

    return g

class IOQueue:
    """
    We mock a server/client situation by creating a pipe object that
    recieves items in a sink, stores them in a synchronised queue
    object, and sends them out again in source. Any number of threads
    or objects may create a sink or source. All pool to the same Queue.

    This implementation serves as an example and to glue the local threaded
    runner together. On one side there is a worker pool, taking jobs from one
    of these queues. On the other side there is the controller taking results
    from a second pipe, the snake biting its tail.
    """
    def __init__(self):
        self.Q = Queue()

    @coroutine_sink
    def sink(self):
        while True:
            r = yield
            self.Q.put(r)

    def source(self):
        while True:
            yield self.Q.get()
            self.Q.task_done()

    def wait(self):
        self.Q.join()

class Connection:
    def __init__(self, source, sink):
        self.source = source
        self.sink   = sink

    def setup(self):
        src = self.source()
        snk = self.sink()
        return src, snk

class QueueConnection(Connection):
    """
    Takes an input and output queue, and conceptually links them,
    returning a pair containing a source from the input queue
    and a sink to the output queue.
    """
    def __init__(self, d_in, d_out):
        super(QueueConnection, self).__init__(d_in.source, d_out.sink)

def merge_sources(*sources):
    def f():
        while True:
            for s in sources:
                v = next(s)
                if v:
                    yield v
            #yield

    return f

def merge_sinks(*sinks):
    @coroutine_sink
    def f():
        while True:
            v = yield

            if not v:
                continue

            for s in sinks:
                s.send(v)

    return f

class Scheduler:
    def __init__(self):
        self.dynamic_links = {}
        self.results = {}
        self.jobs = {}

    def run(self, connection, master):
        # initiate worker slave army and take up reins ...
        source, sink = connection.setup()

        # schedule work
        self.add_workflow(master, master, master.root, sink)

        # process results
        for job_key, result in source:
            wf, n = self.jobs[job_key]

            # if we retrieve a workflow, push a child
            if is_workflow(result):
                child_wf = get_workflow(result)
                self.add_workflow(child_wf, wf, n, sink)
                continue

            # if this result is the root of a workflow, pop to parent
            if n == wf.root:
                _, wf, n = self.dynamic_links[id(wf)]

            # save the result
            self.results[id(wf)][n] = result

            # and insert it in the nodes that need it
            for (tgt, address) in wf.links[n]:
                insert_result(wf.nodes[tgt], address, result)
                if is_node_ready(wf.nodes[tgt]):
                    self.schedule(Job(workflow = wf, node = tgt), sink)

            # see if we're done
            if wf == master and n == master.root:
                return result

    def schedule(self, job, sink):
        uid = uuid.uuid1()
        self.jobs[uid] = job
        sink.send((uid, job.workflow.nodes[job.node]))
        return uid

    def add_workflow(self, wf, target, node, sink):
        self.dynamic_links[id(wf)] = DynamicLink(
            source = wf, target = target, node = node)

        self.results[id(wf)] = dict((n, Empty) for n in wf.nodes)

        depends = invert_links(wf.links)

        for n in wf.nodes:
            if depends[n] == {}:
                self.schedule(Job(workflow = wf, node = n), sink)
