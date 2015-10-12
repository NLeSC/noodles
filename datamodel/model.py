"""
The data model. A workflow consists of nodes and links. The Nodes have to be
derived from the `Node` class. The links are directed. We store the nodes as well
as the links in dictionaries. The nodes are stored in dictionaries to keep
consistency when a node is deleted. The dictionary representation of the links
is easier to search than just a list of pairs. To ease searching the other way
around we also keep a book of inverse links.

The information stored in these objects should be enough to store the workflow
and recover the same working conditions when opening the file. (yaml)
For this purpose we also store the node position and the extent. The extent of a
node in pixels is not something we have control over, but we might want to store
the node layout in terms of a table, alowing for some form of automatic layout.

A node may have multiple input and output connectors. This should be represented
in the data model. In many cases there will be one input, one output connector
passing a dictionary. Even then we will want to be able to merge two dicts
selectively.
"""

#import logging

#logger = logging.getLogger(__name__)
#_ch = logging.StreamHandler()
#_ch.setLevel(logging.INFO)
#_formatter = logging.Formatter("{asctime} - {levelname}: {message}", style="{")
#_ch.setFormatter(_formatter)
#logger.addHandler(_ch)

class NodeTemplate:
#    input_vars = []
#    output_vars = []
    def __init__(self):
        pass

from itertools import chain
from collections import namedtuple

Noodlet  = namedtuple('Noodlet', ['name', 'dtype', 'connector', 'direction', 'widget'])
      
class Node:
    def inuput_noodlets(self):
        """
        Generator for all input items in a node:
            - input noodlets
            - input widgets
            - output widgets
            - output noodlets
        In the simplest case each item will be displayed
        as a label showing the variable name.
        
        -> (str name, str type, bool connector, Maybe[widget-hint])
        
        The type should be indicative of the kind of widget
        that would be suitable to manipulate or display the value.
        
        Possibilities:
            - list-selector:    "A" | "B" | "C"
            - dictionary:       { name: type, ...}
            - list:             [ type ]
            - tuple:            ( type, ... )
            - named-tuple?      ( name: type, ... )
            - table:            [ named-tuple ]
            - primitive (key-words): 
                float, integer, complex, rational
                char, string
        
        For ease of input:    
            - constrained types: 
                range(transformer f), where f: [0,1] -> type
            - prevent mistakes
                check(type, predicate p), where p: type -> bool
                for example: Y_lm -> -l >= m >= l
                
        Output only:
            - image, audio, video
        """
        pass
        
    def output_noodlets(self):
        """
        
        """
        pass
        
class SimpleNode(Node):
    def __init__(self, template):
        self.name = "{name} {number:016X}".format(
            name=template.name, number=id(self))
        self.extent = None          # auto-layout, table spanning
        self.location = None
        self.template = template
        
    def input_noodlets(self):
        for v in self.template.input_vars:
            yield Noodlet(name=v, dtype=int, connector=True, direction='in', widget=False)
        
    def output_noodlets(self):
        for v in self.template.output_vars:
            yield Noodlet(name=v, dtype=int, connector=True, direction='out', widget=False)
        
    def items(self):
        for i in chain(iter(self.template.input_vars),
                        iter(self.template.output_vars)):
            yield i

class DataModel:
    """
    The NoodlesModel contains all data that we want saved between
    sessions. 
    
    This includes information on the location of nodes as the
    user put them down. The extent of a node may be dependent on the
    font sizes and themes of the user. We'd like to be able to draw the
    graph without knowing too much about the way Gtk would render it.
    """
    def __init__(self):
        self._counter = 0
        self._nodes = {}    # list of nodes with attributes of:
                            #    - location -- stored as integers in combination with auto-layout?
                            #    - extent -- also as integers? 
                            #    - name -- unique node identifier
                            #    - input -- list of string identifiers
                            #    - output -- list of string identifiers
                            
        self._links = {}    # links between nodes, given by a dict of type
                            # {(int,str): [(int,str)]}, where ints are indices into
                            # the _nodes list. The receiver and sender can negotiate
                            # a type if they want.
                            
        self._inverse_links = {}   # speeds up searching
        
    def all_nodes(self):
        """
        returns an iterator over all nodes.
        """
        return self._nodes.items()
        
    def all_links(self):
        """
        Generator for a linear list of all links. Should be used like:
        
            for (i,n), (j,m) in model.all_links():
                # here i and j are integer indices to the nodes,
                # and n and m are the i/o variables for these nodes
        """
        for i, lst in self._links.items():
            for j in lst:
                yield (i, j)
        
    def add_node(self, node):
        """
        Adds a node to the data structure. Creates entries into the link
        dictionaries.
        
        Returns: integer handler.
        """
        i = self._counter
        self._counter += 1
        
        self._nodes[i] = node
        
        # make sure empty entries exists in the linking dicts
        for s in node.output_noodlets():
            self._links[(i, s.name)] = set()
        
        for s in node.input_noodlets():
            self._inverse_links[(i, s.name)] = set()
            
        return i

    def add_link(self, a, b):
        self._links[a].add(b)
        self._inverse_links[b].add(a)
        #self._nodes[a].outbound.append(b)
        #self._nodes[b].inbound.append(a)
    
    def delete_link(self, a, b):
        self._links[a].remove(b)
        self._inverse_links[b].remove(a)

    def links_to(self, b):
        return self._inverse_links[b]
                
    def delete_links_to(self, b):
        for a in self._inverse_links[b]:
            self._links[a].remove(b)
        self._inverse_links[b] = set()
        
    def _delete_node_by_index(self, idx):
        # remove connections to the node
        for s in self._nodes[idx].input_noodlets():
            for j in self._inverse_links[(idx, s.name)]:
                try:
                    self._links[j].remove((idx, s.name))
                except ValueError:
                    logger.error(
                        "Found a link in the `_inverse_links` dict" 
                        " that is not represented in the `_links` dict.")
                        
            del self._inverse_links[(idx,s.name)]

        # remove connections from the node
        for s in self._nodes[idx].output_noodlets():
            for j in self._links[(idx,s.name)]:
                try:
                    self._inverse_links[j].remove((idx,s.name))
                except ValueError:
                    logger.error(
                        "Found a link in the `_links` dict" 
                        " that is not represented in the `_inverse_links` dict.")                    

            del self._links[(idx,s.name)]

        # remove the node        
        del self._nodes[idx]
            
    def delete_node(self, node):
        """
        Delete a node. This method covers three cases; where node is
            - `int`, index into the list of nodes
            - `Node`, delete the node using list.remove
            - `str`, search the node, then remove it
        """
        if isinstance(node, int):
            self._delete_node_by_index(node)
            return
            
        if isinstance(node, Node):
            idx = self._nodes.index(node)
            self._delete_node_by_index(idx)
            return
            
        if isinstance(node, str):
            self._delete_node_by_name(node)
            return
            
    def _delete_node_by_name(self, name):
        try:
            self._delete_node_by_index(next(i for i,x 
                in enumerate(self._nodes) 
                if x.name == name))
                
        except StopIteration:
            logger.warning("Tried to delete an non-existing node: '{name}'.".format(name=name))
    
    def _clean_indices(self):
        """
        Remap the indices to a compact range, makes for nicer storage.
        """
        
        # find the mapping between the indices and store it in a dict
        old_to_new_d = dict((v, i) for i, v in enumerate(self._nodes.keys()))
        
        # to map the (int, str) tupled noodlets from old to new have a helper
        old_to_new_f = lambda noodlet: (old_to_new_d[noodlet[0]], noodlet[1])
        
        # remap the nodes
        self._nodes = dict((old_to_new_d[i], v) for i, v in self._nodes)
        
        # remap the links
        self._links = dict((old_to_new_f(ndl1), [old_to_new_f(ndl2) for ndl2 in lst])
                            for ndl1, lst in self._links)
                            
        # remap the inverse links
        self._inverse_links = dict((old_to_new_f(ndl1), [old_to_new_f(ndl2) for ndl2 in lst])
                            for ndl1, lst in self._inverse_links)
        
