from .data_types import Empty
from .data_arguments import set_argument


def reset_workflow(workflow):
    for src, tgt in workflow.links.items():
        for m, a in tgt:
            set_argument(workflow.nodes[m].bound_args, a, Empty)

    return workflow
