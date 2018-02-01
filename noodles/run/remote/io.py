"""
Manage IO between remote worker/pilot job, and the scheduler. Here there are
two options: use json, or msgpack.
"""

from ...lib import coroutine


def JSONObjectReader(registry, fi, deref=False):
    """Stream objects from a JSON file.

    :param registry: serialisation registry.
    :param fi: input file
    :param deref: flag, if True, objects will be dereferenced on decoding,
        otherwise we are lazy about decoding a JSON string.
    """
    for line in fi:
        yield registry.from_json(line, deref=deref)


@coroutine
def JSONObjectWriter(registry, fo, host=None):
    """Sink; writes object as JSON to a file.

    :param registry: serialisation registry.
    :param fo: output file.
    :param host: name of the host that encodes the JSON. This is relevant if
        the encoded data refers to external files for mass storage.

    In normal use, it may occur that the pipe to which we write is broken,
    for instance when the remote process shuts down. In that case, this
    coroutine exits.
    """
    while True:
        obj = yield
        try:
            print(registry.to_json(obj, host=host), file=fo, flush=True)
        except BrokenPipeError:
            return
