"""
Implements serialisers for Numpy objects.
"""

import uuid
import io
import base64
import hashlib

import filelock
import h5py
import numpy

from .registry import (Serialiser, Registry)
from ..lib import look_up


class SerNumpyArray(Serialiser):
    """Serialise Numpy array as a Base64 file."""
    def __init__(self):
        super(SerNumpyArray, self).__init__(numpy.ndarray)

    def encode(self, obj, make_rec):
        fo = io.BytesIO()
        numpy.save(fo, obj, allow_pickle=False)
        return make_rec(base64.b64encode(fo.getvalue()).decode())

    def decode(self, cls, data):
        fi = io.BytesIO(base64.b64decode(data.encode()))
        return numpy.load(fi)


class SerNumpyScalar(Serialiser):
    """Serialises a Numpy scalar by storing bytes."""
    def __init__(self):
        super(SerNumpyScalar, self).__init__('<numpy-scalar>')

    def encode(self, obj, make_rec):
        return make_rec({
            'dtype': str(obj.dtype),
            'bytes': obj.tobytes()})

    def decode(self, cls, data):
        return numpy.frombuffer(data['bytes'], dtype=data['dtype'])[0]


class SerNumpyArrayToFile(Serialiser):
    """Serialises a Numpy array to a .npy file."""
    def __init__(self, file_prefix=None):
        super(SerNumpyArrayToFile, self).__init__(numpy.ndarray)
        self.file_prefix = file_prefix if file_prefix else ''

    def encode(self, obj, make_rec):
        filename = self.file_prefix + str(uuid.uuid4()) + '.npy'
        numpy.save(filename, obj)
        return make_rec(filename, ref=True, files=[filename])

    def decode(self, cls, data):
        return numpy.load(data)


def array_sha256(a):
    """Create a SHA256 hash from a Numpy array."""
    dtype = str(a.dtype).encode()
    shape = numpy.array(a.shape)
    sha = hashlib.sha256()
    sha.update(dtype)
    sha.update(shape)
    sha.update(a.tobytes())
    return sha.hexdigest()


class SerNumpyArrayToHDF5(Serialiser):
    """Serialises Numpy array to HDF5 file."""
    def __init__(self, filename, lockfile):
        super(SerNumpyArrayToHDF5, self).__init__(numpy.ndarray)
        self.filename = filename
        self.lock = filelock.FileLock(lockfile)

    def encode(self, obj, make_rec):
        key = array_sha256(obj)
        with self.lock:
            f = h5py.File(self.filename)
            path = next(
                (ds for ds in f if f[ds].attrs.get('hash') == key),
                False)
            if not path:
                path = base64.b64encode(uuid.uuid4().bytes).decode()
                dataset = f.create_dataset(
                    path, shape=obj.shape, dtype=obj.dtype)
                dataset[...] = obj
                dataset.attrs['hash'] = key
                f.close()

        return make_rec({
            "filename": self.filename,
            "path": path
        }, files=[self.filename], ref=True)

    def decode(self, cls, data):
        with self.lock:
            f = h5py.File(self.filename)
            obj = f[data["path"]].value
            f.close()

        return obj


class SerUFunc(Serialiser):
    """Serialiser for Numpy UFuncs."""
    def __init__(self):
        super(SerUFunc, self).__init__(None)

    def encode(self, obj, make_rec):
        return make_rec('numpy.' + obj.name)

    def decode(self, cls, data):
        return look_up(data)


def _numpy_hook(obj):
    """If an object is a ufunc, return '<ufunc>'"""
    if isinstance(obj, numpy.ufunc):
        return '<ufunc>'

    return None


def arrays_to_file(file_prefix=None):
    """Returns a serialisation registry for serialising NumPy data and
    as well as any UFuncs that have no normal way of retrieving
    qualified names."""
    return Registry(
        types={
            numpy.ndarray: SerNumpyArrayToFile(file_prefix)
        },
        hooks={
            '<ufunc>': SerUFunc()
        },
        hook_fn=_numpy_hook
    )


def arrays_to_string(file_prefix=None):
    """Returns registry for serialising arrays as a Base64 string."""
    return Registry(
        types={
            numpy.ndarray: SerNumpyArray(),
            numpy.floating: SerNumpyScalar()
        },
        hooks={
            '<ufunc>': SerUFunc()
        },
        hook_fn=_numpy_hook
    )


def arrays_to_hdf5(filename="cache.hdf5"):
    """Returns registry for serialising arrays to a HDF5 reference."""
    return Registry(
        types={
            numpy.ndarray: SerNumpyArrayToHDF5(filename, "cache.lock")
        },
        hooks={
            '<ufunc>': SerUFunc()
        },
        hook_fn=_numpy_hook
    )


registry = arrays_to_string
