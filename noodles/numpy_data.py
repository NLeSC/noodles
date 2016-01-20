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
        super(NumpyData, self).__init__(use_ref=True, files=[])

        self.data = data
        self.filename = filename if filename \
            else (str(uuid.uuid4()) + '.npy')

        # register filename
        self.files.append(self.filename)

    @classmethod
    def from_dict(cls, filename):
        return NumpyData(np.load(filename), filename)

    def as_dict(self):
        np.save(self.filename, self.data)
        return {'filename': self.filename}
