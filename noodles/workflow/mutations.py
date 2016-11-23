from .arguments import set_argument, Empty


def reset_workflow(workflow):
    for tgt in workflow.links.values():
        for m, a in tgt:
            set_argument(workflow.nodes[m].bound_args, a, Empty)

    return workflow


def insert_result(node, address, value):
    """Runs `set_argument`, but checks first wether the data location is not
    already filled with some data. In any normal circumstance this checking
    is redundant, but if we don't give an error here the program would continue
    with unexpected results.
    """
    # a = ref_argument(node.bound_args, address)
    # if a != Empty:
    #    raise RuntimeError(
    #        "Noodle panic. Argument {arg} in {name} already given." \
    #        .format(arg=format_address(address),
    #                name=node.foo.__name__))

    set_argument(node.bound_args, address, value)
