def find_links_to(links, node):
    """
    Find links to a node.

    :param links:
        forward links of a workflow
    :type links: Mapping[NodeId, Set[(NodeId, ArgumentType, [int|str]])]

    :param node:
        index to a node
    :type node: int

    :returns:
        dictionary of sources for each argument
    :rtype: Mapping[(ArgumentType, [int|str]), NodeId]
    """
    return {address: src
            for src, (tgt, address) in _all_valid(links)
            if tgt == node}


def _all_valid(links):
    """
    Iterates over all links, forgetting emtpy registers.
    """
    for k, v in links.items():
        for i in v:
            yield k, i


def invert_links(links):
    """
    Inverts the call-graph to get a dependency graph. Possibly slow,
    short version.

    :param links:
        forward links of a call-graph.
    :type links: Mapping[NodeId, Set[(NodeId, ArgumentType, [int|str]])]

    :returns:
        inverted graph, giving dependency of jobs.
    :rtype: Mapping[NodeId, Mapping[(ArgumentType, [int|str]), NodeId]]
    """
    return {node: find_links_to(links, node) for node in links}
