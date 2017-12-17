"""
Manage IO between remote worker/pilot job, and the scheduler. Here there are
two options: use json, or msgpack.
"""

from ..coroutine import coroutine
from ..connection import EndOfWork

try:
    import msgpack
except ImportError:
    pass


def MsgPackObjectReader(registry, fi, deref=False):
    yield from msgpack.Unpacker(
        fi, object_hook=lambda o: registry.decode(o, deref),
        encoding='utf-8')


@coroutine
def MsgPackObjectWriter(registry, fo, host=None):
    while True:
        obj = yield

        if obj is EndOfWork:
            return

        fo.write(registry.to_msgpack(obj, host=host))
        fo.flush()


def JSONObjectReader(registry, fi, deref=False):
    for line in fi:
        yield registry.from_json(line, deref=deref)


@coroutine
def JSONObjectWriter(registry, fo, host=None):
    # import sys
    while True:
        obj = yield

        if obj is EndOfWork:
            return
        # obj_msg = registry.to_json(obj, host=host)
        # print(obj_msg, file=sys.stderr)
        print(registry.to_json(obj, host=host), file=fo, flush=True)
