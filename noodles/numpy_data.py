from .storable import Storable
import numpy as np
import uuid


class NumpyData(Storable):
    """
    Stores Numpy data as a local resource. This assumes that a single
    filename is enough to retrieve the data from every location where this
    data maybe needed. If you want more advanced behaviour, use the Xenon
    layer (which is NYI ;).
    """
    def __init__(self, data, filename=None):
        super(NumpyData, self).__init__(use_ref=True)

        self.data = data
        self.filename = filename if filename \
            else (str(uuid.uuid4()) + '.npy')

    @classmethod
    def from_dict(cls, filename):
        obj = cls.__new__(cls)
        super(NumpyData, obj).__init__(use_ref=True)

        obj.filename = filename
        obj.data = np.load(filename)
        return obj

    def as_dict(self):
        np.save(self.filename, self.data)
        return {'filename': self.filename}
