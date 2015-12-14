from .data_types import Node, Workflow, Empty, is_workflow, get_workflow
from .data_arguments import (bind_arguments, get_arguments,
                             serialize_arguments, ref_argument,
                             set_argument)

from inspect import signature, getmodule, Parameter
from importlib import import_module
from copy import deepcopy


def unwrap(f):
    try:
        return f.__wrapped__
    except AttributeError:
        return f


def look_up(module, name):
    """
    Import the object named by `name` from the module named by
    `module`.
    """
    M = import_module(module)
    return getattr(M, name)


def module_and_name(f):
    """
    Retrieve the module and name of the given object.
    """
    return getmodule(f).__name__, f.__name__


def importable(x):
    """
    Checks whether we can get import the object and get the same.

    .. code-block:: python

        x == look_up(*module_and_name(x))

    :param x:
        Any object.

    :returns:
        True if `x` can be imported.
    :rtype: bool
    """
    try:
        module, name = module_and_name(x)
        # return look_up(module, name) == x
        # the previous expression doesn't actually work, there
        # seems to be no reasonable way to implement this function.
        return True

    except:
        return False


class FunctionNode:
    """
    Captures a function call as a combination of function and arguments.
    Some of these arguments may be set to :py:obj:`Empty`, these need to be
    filled in by the workflow before the function can be applied.

    .. py:attribute:: foo

    The function (or object) that is being called.

    .. py:attribute:: bound_args

    A :py:class:`BoundArguments` object storing the arguments to
    the function.
    """
    @staticmethod
    def from_node(node):
        foo = unwrap(look_up(node.module, node.name))
        bound_args = bind_arguments(foo, node.arguments)
        return FunctionNode(foo, bound_args, node.hints, node)

    def __init__(self, foo, bound_args, hints, node=None):
        self.foo = foo
        self.bound_args = bound_args
        self.hints = hints
        self._node = node

    def node(self):
        """
        Convert to a :py:class:`Node` for subsequent serialisation.
        """
        module, name = module_and_name(self.foo)
        arguments = get_arguments(self.bound_args)
        self._node = Node(module, name, arguments, self.hints)
        return self._node


def from_call(foo, args, kwargs, hints):
    """
    Takes a function and a set of arguments it needs to run on. Returns a newly
    constructed workflow representing the promised value from the evaluation of
    the function with said arguments.

    These arguments are stored in a BoundArguments object matching to the
    signature of the given function `f`. That is, bound_args was constructed
    by doing:

    .. code-block:: python

        inspect.signature(foo).bind(*args, **kwargs)

    The arguments stored in the `bound_args` object are filtered on being
    either 'plain', or 'promised'. If an argument is promised, the value
    it represents is not actually available and needs to be computed by
    evaluating a workflow.

    If an argument is a promised value, the workflow representing the value
    is added to the new workflow. First all the nodes in the original workflow,
    if not already present in the new workflow from an earlier argument,
    are copied to the new workflow, and a new entry is made into the link
    dictionary. Then the links in the old workflow are also added to the
    link dictionary. Since the link dictionary points from nodes to a `set`
    of `ArgumentAddress`es, no links are duplicated.

    In the `bound_args` object the promised value is replaced by the `Empty`
    object, so that we can see which arguments still have to be evaluated.

    Doing this for all promised value arguments in the bound_args object,
    results in a new workflow with all the correct dependencies represented
    as links in the graph.

    :param bound_args:
        Object containing the argument bindings for the function that is
        being called.
    :type bound_args: BoundArguments

    :param f:
        Function being called.
    :type f: Callable

    :returns:
        New workflow.
    :rtype: Workflow
    """
    bound_args = signature(foo).bind(*args, **kwargs)
    bound_args.apply_defaults()

    variadic = next((x.name
                    for x in bound_args.signature.parameters.values()
                    if x.kind == Parameter.VAR_POSITIONAL), None)

    # *HACK*
    # the BoundArguments class uses a tuple to store the
    # variadic arguments. Since we need to modify them,
    # we have to replace the tuple with a list. This works, for now...
    if variadic:
        bound_args.arguments[variadic] = list(bound_args.arguments[variadic])

    node = FunctionNode(foo, bound_args, hints)

    root = id(node)
    nodes = {root: node}
    links = {root: set()}

    for address in serialize_arguments(node.bound_args):
        arg = ref_argument(node.bound_args, address)

        # the argument may still become a workflow if it
        # is a Storable and it contains a promised object
        if not is_workflow(arg):
            arg = deepcopy(arg)

        # if still not a workflow, we have a plain value!
        if not is_workflow(arg):
            set_argument(node.bound_args, address, arg)
            continue

        workflow = get_workflow(arg)
        set_argument(node.bound_args, address, Empty)
        for n in workflow.nodes:
            if n not in nodes:
                nodes[n] = workflow.nodes[n]
                links[n] = set()

            links[n].update(workflow.links[n])

        links[workflow.root].add((root, address))

    return Workflow(root, nodes, links)
