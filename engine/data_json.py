"""
Functions for storing a |Workflow| as a JSON stream.
"""

from .data_types import *
from .data_arguments import *
from .data_node import *
from .data_workflow import *

import json
from itertools import count
from inspect import isfunction

def json_sauce(x):
    if importable(x):
        module, name = module_and_name(x)
        return { '_noodles': { 'type':   'importable',
                               'module': module,
                               'name':   name } }

    raise TypeError

def json_desauce(x):
    if not '_noodles' in x:
        return x

    obj = x['_noodles']
    if obj['type'] == 'importable':
        return look_up(obj['module'], obj['name'])

def address_to_jobject(a):
    return { 'kind':  a.kind.name,
             'name':  a.name,
             'key':   a.key }

def node_to_jobject(node):
    return { 'module':    node.module,
             'name':      node.name,
             'arguments': [ { 'address' : address_to_jobject(a),
                              'value'   : v }
                              for a, v in node.arguments ] }

def _remap_links(remap, links):
    return [ { 'node': remap[source],
               'to':   [ { 'node'    : remap[node],
                           'address' : address_to_jobject(address) }
                           for node, address in target ] }
               for source, target in links.items() ]

def _remap_nodes(remap, nodes):
    return [node_to_jobject(n.node()) for n in nodes.values()]

def workflow_to_jobject(workflow):
    """
    Converts a workflow to a structure that is JSON storable. This is the
    inverse of |jobject_to_workflow|. Node identities are remapped to more
    friendly numbers [0..(N-1)].
    """
    remap = dict(zip(workflow.nodes.keys(), count()))

    return { 'root'  : remap[workflow.root],
             'nodes' : _remap_nodes(remap, workflow.nodes),
             'links' : _remap_links(remap, workflow.links) }

def jobject_to_address(jobj):
    return ArgumentAddress(
        ArgumentKind[jobj['kind']],
        jobj['name'],
        jobj['key'])

def jobject_to_node(jobj):
    arguments = [(jobject_to_address(a['address']), a['value'])
                    for a in jobj['arguments']]

    return FunctionNode.from_node(
        Node(jobj['module'], jobj['name'], arguments))

def jobject_to_workflow(jobj):
    """
    Converts a JSON object (the result of |json.loads|) to a functioning
    workflow. Doing `jobject_to_workflow(workflow_to_jobject(wf))`
    should give an equivalent workflow.
    """
    root  = jobj['root']

    nodes = dict(zip(count(), (jobject_to_node(n)
                    for n in jobj['nodes'])))

    links = dict((l['node'], set((
                            target['node'],
                            jobject_to_address(target['address']))
                        for target in l['to']))
                    for l in jobj['links'])

    return reset_workflow(Workflow(root, nodes, links))

def workflow_to_json(workflow):
    return json.dumps(workflow_to_jobject(workflow), default = json_sauce)

def json_to_workflow(s):
    return jobject_to_workflow(json.loads(s, object_hook = json_desauce))
