"""
Manage IO between remote worker/pilot job, and the scheduler. Here there are
two options: use json, or msgpack.
"""

from ...lib import coroutine
from ..messages import EndOfWork

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
        try:
            fo.write(registry.to_msgpack(obj, host=host))
            fo.flush()
        except BrokenPipeError:
            return


def JSONObjectReader(registry, fi, deref=False):
    for line in fi:
        yield registry.from_json(line, deref=deref)


@coroutine
def JSONObjectWriter(registry, fo, host=None):
    # import sys
    while True:
        obj = yield
        # obj_msg = registry.to_json(obj, host=host)
        # print(obj_msg, file=sys.stderr)
        try:
            print(registry.to_json(obj, host=host), file=fo, flush=True)
        except BrokenPipeError:
            return

