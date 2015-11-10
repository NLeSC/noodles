from .data_types import *
from .data_arguments import *
from .data_node import *

import json
from itertools import count

def address_to_object(a):
    return { 'kind':  a.kind.name,
             'name':  a.name,
             'key':   a.key }

def node_to_object(node):
    return { 'module':    node.module,
             'name':      node.name,
             'arguments': [{ 'address': address_to_object(a),
                             'value':   v } for a, v in node.arguments] }

def remap_links(remap, links):
    return [ { 'node': remap[source],
               'to':   [ { 'node':    remap[node],
                           'address': address_to_object(address) }
                             for node, address in target ] }
                for source, target in links.items() ]

def remap_nodes(remap, nodes):
    return dict((remap[i], node_to_object(n.node()))
                  for i, n in nodes.items())

def workflow_to_object(workflow):
    remap = dict(zip(workflow.nodes.keys(), count()))

    return { "root"  : remap[workflow.root],
             "nodes" : remap_nodes(remap, workflow.nodes),
             "links" : remap_links(remap, workflow.links) }

def workflow_to_json(workflow):
    return json.dumps(workflow_to_object(workflow),
                sort_keys = True, indent = 2)
