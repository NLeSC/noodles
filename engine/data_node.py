from .data_types import *

def node_function(node):
    if is_instance(node, FunctionNode):
        return node.foo

    if is_instance(node, Node):
        return look_up(node.module, node.name)

def node_arguments(node):
    if is_instance(node, FunctionNode):
        return node.bound_args

    if is_instance(node, Node):
        return reconstruct_arguments(
            look_up(node.module, node.name),
            node.arguments)
