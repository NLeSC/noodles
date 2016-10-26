from ..workflow import (Workflow, is_node_ready, Empty)
from ..workflow.arguments import (serialize_arguments, ref_argument)
from ..serial import (Registry)
from .prov import (prov_key)


def links(wf, i, deps):
    for d in deps:
        for l in wf.links[d]:
            if l[0] == i:
                yield (l[1], wf.nodes[d].prov)


def empty_args(n):
    for arg in serialize_arguments(n.bound_args):
        if ref_argument(n.bound_args, arg) == Empty:
            yield arg


def set_global_provenance(wf: Workflow, registry: Registry):
    """Compute a global provenance key for the entire workflow
    before evaluation. This key can be used to store and retrieve
    results in a database. The key computed in this stage is different
    from the (local) provenance key that can be computed for a node
    if all its arguments are known.

    In cases where a result derives from other results that were
    computed in child workflows, we can prevent the workflow system
    from reevaluating the results at each step to find that we already
    had the end-result somewhere. This is where the global prov-key
    comes in.

    Each node is assigned a `prov` attribute. If all arguments for this
    node are known, this key will be the same as the local prov-key.
    If some of the arguments are still empty, we add the global prov-keys
    of the dependent nodes to the hash.

    In this algorithm we traverse from the bottom of the DAG to the top
    and back using a stack. This allows us to compute the keys for each
    node without modifying the node other than setting the `prov` attribute
    with the resulting key."""
    stack = [wf.root]

    while stack:
        i = stack.pop()
        n = wf.nodes[i]

        if n.prov:
            continue

        if is_node_ready(n):
            job_msg = registry.deep_encode(n)
            n.prov = prov_key(job_msg)
            continue

        deps = wf.inverse_links[i]
        todo = [j for j in deps if not wf.nodes[j].prov]

        if not todo:
            link_dict = dict(links(wf, i, deps))
            link_prov = registry.deep_encode(
                [link_dict[arg] for arg in empty_args(n)])
            job_msg = registry.deep_encode(n)
            n.prov = prov_key(job_msg, link_prov)
            continue

        stack.append(i)
        stack.extend(deps)
