from .registry import (Serialiser, Registry)

import base64
import pickle


class PickleString(Serialiser):
    def __init__(self, cls):
        super(PickleString, self).__init__(cls)

    def encode(self, obj, make_rec):
        data = base64.b64encode(pickle.dumps(obj)).decode('ascii')
        return make_rec(data)

    def decode(self, cls, data):
        return pickle.loads(base64.b64decode(data.encode('ascii')))


def registry():
    """Returns a serialisation registry that "just pickles everything".

    This registry can be used to bolt-on other registries and keep the
    pickle as the default. The objects are first pickled to a byte-array,
    which is subsequently encoded with base64."""
    return Registry(
        default=PickleString(object)
    )
