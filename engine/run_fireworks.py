from fireworks import FireTaskBase
from fireworks.utilities.fw_utilities import explicit_serialize

try:
    import dill as pickle
except ImportError:
    import pickle

from .datamodel import *

@explicit_serialize
class NoodlesTask(FireTaskBase):
    def run_task(self, fw_spec):
