from inspect import (signature, Parameter)
from .model import (
    Workflow, FunctionNode, get_workflow, is_workflow)
from .arguments import (
    ref_argument, serialize_arguments, set_argument, Empty)

from copy import deepcopy


def from_call(foo, args, kwargs, hints, call_by_value=True):
    """Takes a function and a set of arguments it needs to run on. Returns a newly
    constructed workflow representing the promised value from the evaluation of
    the function with said arguments.

    These arguments are stored in a BoundArguments object matching to the
    signature of the given function ``foo``. That is, bound_args was
    constructed by doing:

    ::

        inspect.signature(foo).bind(*args, **kwargs)

    The arguments stored in the ``bound_args`` object are filtered on being
    either plain, or promised. If an argument is promised, the value
    it represents is not actually available and needs to be computed by
    evaluating a workflow.

    If an argument is a promised value, the workflow representing the value
    is added to the new workflow. First all the nodes in the original workflow,
    if not already present in the new workflow from an earlier argument,
    are copied to the new workflow, and a new entry is made into the link
    dictionary. Then the links in the old workflow are also added to the
    link dictionary. Since the link dictionary points from nodes to a
    :py:class:`set` of :py:class:`ArgumentAddress` es, no links are
    duplicated.

    In the ``bound_args`` object the promised value is replaced by the
    ``Empty`` object, so that we can see which arguments still have to be
    evaluated.

    Doing this for all promised value arguments in the bound_args object,
    results in a new workflow with all the correct dependencies represented
    as links in the graph.

    :param foo:
        Function (or object) being called.
    :type foo: Callable

    :param args:
        Normal arguments to call

    :param kwargs:
        Keyword arguments to call

    :param hints:
        Hints that can be passed to the scheduler on where or how
        to schedule this job.

    :returns:
        New workflow.
    :rtype: Workflow
    """
    # create the bound_args object
    bound_args = signature(foo).bind(*args, **kwargs)
    bound_args.apply_defaults()

    # get the name of the variadic argument if there is one
    variadic = next((x.name
                     for x in bound_args.signature.parameters.values()
                     if x.kind == Parameter.VAR_POSITIONAL), None)

    # *HACK*
    # the BoundArguments class uses a tuple to store the
    # variadic arguments. Since we need to modify them,
    # we have to replace the tuple with a list. This works, for now...
    if variadic:
        if variadic not in bound_args.arguments:
            bound_args.arguments[variadic] = []
        else:
            bound_args.arguments[variadic] = \
                list(bound_args.arguments[variadic])

    # create the node and initialise hash key
    node = FunctionNode(foo, bound_args, hints)

    # setup the new workflow
    root = id(node)
    nodes = {root: node}
    links = {root: set()}

    # walk the arguments to the function call
    for address in serialize_arguments(node.bound_args):
        arg = ref_argument(node.bound_args, address)

        # the argument may still become a workflow if it
        # is a Storable and it contains a promised object
        if not is_workflow(arg) and call_by_value:
            arg = deepcopy(arg)

        # if still not a workflow, we have a plain value!
        if not is_workflow(arg):
            set_argument(node.bound_args, address, arg)
            continue

        # merge the argument workflow into the new workflow
        workflow = get_workflow(arg)
        set_argument(node.bound_args, address, Empty)
        for n in workflow.nodes:
            if n not in nodes:
                nodes[n] = workflow.nodes[n]
                links[n] = set()

            links[n].update(workflow.links[n])

        links[workflow.root].add((root, address))

    return Workflow(root, nodes, links)
