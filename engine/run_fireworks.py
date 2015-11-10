

#================> Python Standard  and third-party <==========

from importlib import import_module

## ================ FireWorks modules  ==================
from fireworks import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable

#==================> Internal modules <==========
from .datamodel import *

#====================<>===============================
class NoodlesTask(FireTaskBase,FWSerializable):
    """
    Runs a task.
    """

    def run_task(self, fw_spec):

        workflow               = TODO
        root_ref, nodes, links = workflow

        #Root Case
        fun_node = nodes[root_ref]
        fun      = fun_node.foo 
        args     = [ref_argument() for address in fun_node.bound_args]
        fw1 = PyTask(fun_node.foo)

    
        ## ith-case 
        
        for address in serialize_arguments(bound_args):
            workflow = get_workflow(
                ref_argument(bound_args, address))

            if not workflow:
                continue
        

    # def run_task(self, fw_spec):
    #     argkeys      = fw_spec['args']
    #     imports_spec = fw_spec['import_spec']
    #     foo          = fw_spec['function']
    #     args = dict((name, fw_spec[key]) for key, name in argkeys.values())


    #     env = load_environment(import_spec)
    #     result = env.apply_function(foo, args)



        
# class Environment:
#     def __init__(globals = {}, locals = {}):
#         self.globals = globals
#         self.locals = locals

#     def simple_import(module):
#         self.locals[module] = import_module(module)

#     def import_module(module, base, import_as):
#         self.locals[import_as] = import_module(module, base)

#     def from_module_import(module, base, import_dict):
#         tmp = import_module(module, base)
#         for k, v in import_dict.items():
#             self.locals[v] = tmp[k]

#     def apply_function(foo, *args, **kwargs):
#         self.locals['args']   = args
#         self.locals['kwargs'] = kwargs
#         return eval("{foo}(*args, **kwargs)".format(foo = foo),
#             self.globals, self.locals)

# def load_environment(import_spec):
#     env = Environment()
#     for m in import_spec:
#         env.simple_import(m)
#     return env

