from .coroutines import coroutine_sink, Connection
from .data_json import saucer, desaucer, node_to_jobject
from .logger import log

import threading
from subprocess import Popen, PIPE
import json
import uuid


def read_result(s):
    obj = json.loads(s, object_hook=desaucer())
    return (uuid.UUID(obj['key']), obj['result'])


def put_job(host, key, job):
    obj = {'key': key.hex,
           'node': node_to_jobject(job.node())}
    return json.dumps(obj, default=saucer(host))

# processes = {}


def process_worker(verbose=False, jobdirs=False):
    name = "process-" + str(uuid.uuid4())

    cmd = ["python3.5", "-m", "noodles.worker", "online", "-name", name]
    if verbose:
        cmd.append("-verbose")
    if jobdirs:
        cmd.append("-jobdirs")

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

    return Connection(get_result, send_job)
