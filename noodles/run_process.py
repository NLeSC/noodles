from .coroutines import coroutine_sink, Connection
from .data_json import json_sauce, json_desauce, node_to_jobject
from subprocess import Popen, PIPE
import json
import uuid


def read_result(s):
    obj = json.loads(s, object_hook=json_desauce)
    return (uuid.UUID(obj['key']), obj['result'])


def put_job(key, job):
    obj = {'key': key.hex,
           'node': node_to_jobject(job.node())}
    return json.dumps(obj, default=json_sauce)


def process_worker():
    p = Popen(
        ["python3.5", "-m", "noodles.worker", "online"],
        stdin=PIPE, stdout=PIPE, universal_newlines=True)

    @coroutine_sink
    def send_job():
        while True:
            key, job = yield
            print(put_job(key, job), file=p.stdin, flush=True)

    def get_result():
        for line in p.stdout:
            key, result = read_result(line)
            yield (key, result)

    return Connection(get_result, send_job)
