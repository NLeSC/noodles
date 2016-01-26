"""
Functions for storing a |Workflow| as a JSON stream.

A Workflow is stored as with `root`, `nodes` and `links`. The `nodes` contain
a list of all nodes. And `links` is an object containing `node`, indexing
the source node and `to`, a list of indices to target nodes. When we reload
a workflow the node ids will not be conserved.

A Node contains a reference to some Python function or object. This part is
stored as the `module` and `name` needed to reimport this. Second the node
stores all arguments needed to make the function call. These arguments should
either be a primitive value, an importable object or an instance of a class
derived from `Storable`.
"""

from .data_types import (Workflow, ArgumentAddress, ArgumentKind, Node,
                         is_workflow, get_workflow)
from .data_node import FunctionNode, importable, module_and_name, look_up
from .data_workflow import reset_workflow
from .storable import storable, StorableRef
from .deepmap import deep_map

import json
from itertools import count


def saucer(host=None):
    def json_sauce(x):
        if is_workflow(x):
            return {'_noodles': {'type': 'workflow',
                                 'data': workflow_to_jobject(get_workflow(x))}}

        if storable(x) and importable(type(x)):
            module, name = module_and_name(type(x))
            return {'_noodles': {'type': 'storable',
                                 'use_ref': x._use_ref,
                                 'host': host,
                                 'files': x._files,
                                 'module': module,
                                 'name': name},
                    'data': deep_map(value_to_jobject, x.as_dict())}

        if isinstance(x, StorableRef):
            return x.data

        if hasattr(x, '__member_of__') and x.__member_of__ is not None:
            module, class_name = module_and_name(x.__member_of__)
            method_name = x.__name__
            return {'_noodles': {'type': 'method',
                                 'module': module,
                                 'class': class_name,
                                 'name': method_name}}

        if importable(x):
            module, name = module_and_name(x)
            return {'_noodles': {'type': 'importable',
                                 'module': module,
                                 'name': name}}

        raise TypeError("type: {}, value: {}".format(type(x), str(x)))

    return json_sauce


def desaucer(deref=False):
    def json_desauce(x):
        if '_noodles' not in x:
            return x

        obj = x['_noodles']
        if obj['type'] == 'importable':
            return look_up(obj['module'], obj['name'])

        if obj['type'] == 'storable':
            if obj['use_ref']:
                if deref:
                    return StorableRef(x).make()
                return StorableRef(x)

            cls = look_up(obj['module'], obj['name'])
            data = x['data']
            return cls.from_dict(**data)

        if obj['type'] == 'autostorable':
            cls = look_up(obj['module'], obj['name'])
            data = x['data']
            return cls.from_dict(**data)

        if obj['type'] == 'dict':
            cls = look_up(obj['module'], obj['name'])
            data = x['data']
            return cls(data)

        if obj['type'] == 'workflow':
            return jobject_to_workflow(obj['data'])

        if obj['type'] == 'method':
            cls = look_up(obj['module'], obj['class'])
            return getattr(cls, obj['name'])

    return json_desauce


def address_to_jobject(a):
    return {'kind':  a.kind.name,
            'name':  a.name,
            'key':   a.key}


def value_to_jobject(v):
    #if hasattr(v, '_noodles') and v._noodles.get('do_not_touch', False):
    #    return v

    if isinstance(v, dict) and type(v) != dict:
        module, name = module_and_name(type(v))
        return {'_noodles': {'type': 'dict',
                             'module': module,
                             'name': name},
                'data': dict(v)}

    if not storable(v) and hasattr(v, 'as_dict') \
            and hasattr(type(v), 'from_dict'):
        module, name = module_and_name(type(v))
        return {'_noodles': {'type': 'autostorable',
                             'module': module,
                             'name': name},
                'data': v.as_dict()}

    return v


def node_to_jobject(node):
    return {'function':  node.function,
            'arguments': [{'address': address_to_jobject(a),
                           'value':   deep_map(value_to_jobject, v)}
                          for a, v in node.arguments],
            'hints':     node.hints}


def _remap_links(remap, links):
    return [{'node': remap[source],
             'to':   [{'node':    remap[node],
                       'address': address_to_jobject(address)}
                      for node, address in target]}
            for source, target in links.items()]


def _remap_nodes(remap, nodes):
    return [node_to_jobject(n.node()) for n in nodes.values()]


def workflow_to_jobject(workflow):
    """
    Converts a workflow to a structure that is JSON storable. This is the
    inverse of |jobject_to_workflow|. Node identities are remapped to more
    friendly numbers [0..(N-1)].
    """
    remap = dict(zip(workflow.nodes.keys(), count()))

    return {'root':  remap[workflow.root],
            'nodes': _remap_nodes(remap, workflow.nodes),
            'links': _remap_links(remap, workflow.links)}


def jobject_to_address(jobj):
    return ArgumentAddress(
        ArgumentKind[jobj['kind']],
        jobj['name'],
        jobj['key'])


def jobject_to_node(jobj):
    arguments = [(jobject_to_address(a['address']), a['value'])
                 for a in jobj['arguments']]

    return FunctionNode.from_node(
        Node(jobj['function'], arguments, jobj['hints']))


def jobject_to_workflow(jobj):
    """
    Converts a JSON object (the result of |json.loads|) to a functioning
    workflow. Doing `jobject_to_workflow(workflow_to_jobject(wf))`
    should give an equivalent workflow.
    """
    root = jobj['root']

    nodes = dict(zip(count(), (jobject_to_node(n)
                 for n in jobj['nodes'])))

    links = dict((l['node'],
                  set((target['node'],
                       jobject_to_address(target['address']))
                      for target in l['to']))
                 for l in jobj['links'])

    return reset_workflow(Workflow(root, nodes, links))


def workflow_to_json(workflow, host=None, **kwargs):
    return json.dumps(workflow_to_jobject(workflow),
                      default=saucer(host), **kwargs)


def json_to_workflow(s, deref=False):
    """Takes a JSON string and converts it to a workflow.

    :param s:
        A JSON string

    :param deref:
        If the workflow contains Storable objects that were loaded by
        reference, this parameter determines wether to instantiate them.
        This should only be True if the process intends to evaluate the
        Workflow.
    :type deref: bool

    :returns:
        A workflow
    :rtype: Workflow
    """

    return jobject_to_workflow(
        json.loads(s, object_hook=desaucer(deref)))
