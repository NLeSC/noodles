from .coroutines import coroutine_sink, Connection
from .data_json import saucer, desaucer, node_to_jobject
from .logger import log

import threading
from subprocess import Popen, PIPE
import json
import uuid


def read_result(s):
    obj = json.loads(s, object_hook=desaucer())
    key = obj['key']
    try:
        key = uuid.UUID(key)
    except ValueError:
        pass

    return key, obj['result']


def put_job(host, key, job):
    obj = {'key': key if isinstance(key, str) else key.hex,
           'node': node_to_jobject(job.node())}
    return json.dumps(obj, default=saucer(host))

# processes = {}


def process_worker(verbose=False, jobdirs=False, init=None, finish=None):
    name = "process-" + str(uuid.uuid4())

    cmd = ["python3.5", "-m", "noodles.worker", "online", "-name", name]
    if verbose:
        cmd.append("-verbose")
    if jobdirs:
        cmd.append("-jobdirs")
    if init:
        cmd.append("-init")
    if finish:
        cmd.append("-finish")

    p = Popen(
        cmd,
        stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def read_stderr():
        for line in p.stderr:
            log.worker_stderr(name, line)

    t = threading.Thread(target=read_stderr)
    t.daemon = True
    t.start()

#    processes[id(p)] = t

    @coroutine_sink
    def send_job():
        while True:
            key, job = yield
            print(put_job(name, key, job), file=p.stdin, flush=True)

    def get_result():
        for line in p.stdout:
            key, result = read_result(line)
            yield (key, result)

    if init is not None:
        send_job().send(("init", init()._workflow.root_node))
        key, result = next(get_result())
        if key != "init" or not result:
            raise RuntimeError("The initializer function did not succeed on worker.")

    if finish is not None:
        send_job().send(("finish", finish()._workflow.root_node))

    return Connection(get_result, send_job)
