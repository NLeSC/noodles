"""
    @author: Johan Hidding
    @description: Data model 2.0

    The data model works on a basis of delayed execution. The user calls
    decorated functions, building a workflow incrementally. Every node in the
    workflow can be thought of as a _promise_ of a value.

    ### Partial application
    In many cases the user will give a mixture of arguments to a function. Part
    may be ordinary values, part _promises_ from previous calls. We need to
    store the plain values at the node level, and the _promises_ in the shape
    of workflows should be merged to form a new workflow. In a sense this is a
    very fancy form of partial application. The original order of the arguments
    should be preserved in reconstructing the call to the function. To support
    this there are _splice_ functions, that replace items in the arguments with
    markers signifying that these arguments should be got at through the
    workflow.

    ### Memoization
    The user needs not
    worry about the origin of the fulfillment of a _promise_. Most probably
    this value will be computed with some fancy package, but we don't like to
    compute things twice. A result can be cached by a process of memoization.
    Fireworks provides functionality to do this on the lowest level. On the
    high end we need to be aware of this. Functions should be _pure_. This means
    that with the same input, we are guaranteed the same answer.
"""

import inspect
from inspect import signature

from itertools import tee, filterfalse, chain, repeat, count

from .data_types import *
from .data_graph import *
from .data_arguments import *

#==============================================================================#
def is_workflow(x):
    return isinstance(x, Workflow) or ('_workflow' in dir(x))

def get_workflow(x):
    if isinstance(x, Workflow):
        return x

    if '_workflow' in dir(x):
        return x._workflow

    return None
#==============================================================================#

def insert_result(node, address, value):
    """
    Runs `set_argument`, but checks first wether the data location is not
    already filled with some data. In any normal circumstance this checking
    is redundant, but if we don't give an error here the program would continue
    with unexpected results.
    """
    a = ref_argument(node.bound_args, address)
    if a != Parameter.empty:
        raise RuntimeError("Noodle panic. Argument {arg} in " \
                             "{name} already given."            \
                .format(arg=format_address(address), name=node.foo.__name__))

    set_argument(node.bound_args, address, value)

def merge_workflow(f, bound_args):
    """
    Takes a function and a set of arguments it needs to run on. Returns a newly
    constructed workflow representing the promised value from the evaluation of
    the function with said arguments.

    These arguments are stored in a BoundArguments object matching to the
    signature of the given function `f`. That is, bound_args was constructed
    by doing:
        > inspect.signature(f).bind(*args, **kwargs)

    The arguments stored in the `bound_args` object are filtered on being
    either 'plain', or 'promised'. If an argument is promised, the value
    it represents is not actually available and needs to be computed by
    evaluating a workflow.

    If an argument is a promised value, the workflow representing the value
    is added to the new workflow. First all the nodes in the original workflow,
    if not already present in the new workflow from an earlier argument,
    are copied to the new workflow, and a new entry is made into the link
    dictionary. Then the links in the old workflow are also added to the
    link dictionary. Since the link dictionary points from nodes to a _set_
    of `ArgumentAddress`es, no links are duplicated.

    In the `bound_args` object the promised value is replaced by the `empty`
    object, so that we can see which arguments still have to be evaluated.

    Doing this for all promised value arguments in the bound_args object,
    results in a new workflow with all the correct dependencies represented
    as links in the graph.

    @param bound_args:
        Object containing the argument bindings for the function that is
        being called.
    @type bound_args: BoundArguments

    @param f:
        Function being called.
    @type f: Callable

    @returns:
        New workflow.
    @rtype: Workflow
    """
    variadic = next((x.name for x in bound_args.signature.parameters.values()
        if x.kind == Parameter.VAR_POSITIONAL), None)

    # *HACK*
    # the BoundArguments class uses a tuple to store the
    # variadic arguments. Since we need to modify them,
    # we have to replace the tuple with a list. This works, for now...
    if variadic:
        bound_args.arguments[variadic] = list(bound_args.arguments[variadic])

    node = FunctionNode(f, bound_args)

    idx = id(node)
    nodes = {idx: node}
    links = {idx: set()}

    for address in serialize_arguments(bound_args):
        workflow = get_workflow(
            ref_argument(bound_args, address))

        if not workflow:
            continue

        set_argument(bound_args, address, Parameter.empty)
        for n in workflow.nodes:
            if n not in nodes:
                nodes[n] = workflow.nodes[n]
                links[n] = set()

            links[n].update(workflow.links[n])

        links[workflow.top].add((idx, address))

    return Workflow(id(node), nodes, links)

def is_node_ready(node):
    """
    Returns True if none of the argument holders contain any `Empty` object.
    """
    return all(ref_argument(node.bound_args, a) != Parameter.empty
        for a in serialize_arguments(node.bound_args))
