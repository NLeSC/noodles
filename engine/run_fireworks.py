from fireworks import FireTaskBase
from fireworks.utilities.fw_utilities import explicit_serialize

from importlib import import_module

from .datamodel import *

class Environment:
    def __init__(globals = {}, locals = {}):
        self.globals = globals
        self.locals = locals

    def simple_import(module):
        self.locals[module] = import_module(module)

    def import_module(module, base, import_as):
        self.locals[import_as] = import_module(module, base)

    def from_module_import(module, base, import_dict):
        tmp = import_module(module, base)
        for k, v in import_dict.items():
            self.locals[v] = tmp[k]

    def apply_function(foo, *args, **kwargs):
        self.locals['args']   = args
        self.locals['kwargs'] = kwargs
        return eval("{foo}(*args, **kwargs)".format(foo = foo),
            self.globals, self.locals)

def load_environment(import_spec):
    env = Environment()
    for m in import_spec:
        env.simple_import(m)
    return env

@explicit_serialize
class NoodlesTask(FireTaskBase):
    """
    Runs a task.
    """
    def run_task(self, fw_spec):
        imports_spec = fw_spec['import_spec']
        foo          = fw_spec['function']

        env = load_environment(import_spec)
        result = env.apply_function(foo, args)
        
