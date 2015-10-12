#!/usr/bin/python3

import sys, os, inspect
from collections import namedtuple
from itertools import tee, filterfalse

################################################################################
# Data definitions                                                             |
#------------------------------------------------------------------------------+
Runner = namedtuple('Runner', ['top', 'nodes', 'links'])

class Node:
    def __init__(self, f, args):
        self.name = f.__name__
        self.f = f
        self.args = args
        
    def __repr__(self):
        return "{0}-[{1}]".format(self.name, self.args)
        
    def __call__(self, **kwargs):
        return f(**kwargs)

################################################################################
# Graph algorithms                                                             |
#------------------------------------------------------------------------------+
def merge_runners(node, rlst):
    """
    Arguments: the new root node (to be added) and a list of graphs.
    Returns: a new graph with the original list of graphs merged into
    one, detecting identical nodes by their Python object id.
    
    Typically the node is a function to be called, and the list of graphs
    represents the computations that had to be performed to get the
    arguments for the function application.
    """
    idx = id(node)
    nodes = {idx: node}
    links = {idx: set()}
    
    for i, r in rlst:
        for n in r.nodes:
            if not n in nodes:
                nodes[n] = r.nodes[n]
                links[n] = set()
                
            links[n].update(r.links[n])

        links[r.top].add(id(node))
    
    return Runner(id(node), nodes, links)

def simplify_runner(r):
    """
    The nodes are stored by their object id, this makes for an unreadable
    identifier with very large numbers. This function remaps all nodes to
    numbers 1..N, where N is the number of nodes.
    """
    node_map = dict((k, i+1) 
        for i, k in enumerate(r.nodes.keys()))

    nodes = dict((node_map[k], v) 
        for k, v in r.nodes.items())
    links = dict((node_map[k], set([node_map[l] for l in r.links[k]]))
        for k in r.nodes.keys())
    top = node_map[r.top]
    
    return Runner(top, nodes, links)    

################################################################################
# Drawing routines                                                             |
#------------------------------------------------------------------------------+
from pygraphviz import AGraph

def draw_runner(fn, runner):
    sr = simplify_runner(runner)
    dot = AGraph(directed=True) #(comment="Computing scheme")
    for i,n in sr.nodes.items():
        dot.add_node(i, label="{0} \n {1}".format(n.name, n.args))
        
    for i in sr.links:
        for j in sr.links[i]:
            dot.add_edge(i, j)
    dot.layout(prog='dot')

    dot.draw(fn)


################################################################################
# Boiler plate                                                                 |
#------------------------------------------------------------------------------+
def partition(pred, lst):
    t1, t2 = tee(lst)
    return filter(pred, t1), filterfalse(pred, t2)

def schedule(f):
    def wrapped(*args, **kwargs):        
        # match args with argspec
        argdict = {}
        argspec = inspect.getargspec(f)
  
        compute, given = partition(lambda x: isinstance(x[1], Runner),
            zip(argspec.args, args))
        
        n = Node(f, dict(given))
        r = merge_runners(n, list(compute))
        return r
         
    wrapped.__doc__ = f.__doc__
    return wrapped

def bind(*a):
    def binder(*args):
        return list(args)
        
    n = Node(binder, dict())
    r = merge_runners(n, [("arg{0:04}".format(i), v) 
            for i, v in enumerate(a)])
    return r

################################################################################
# START OF EXAMPLE
################################################################################

# define some simple functions

@schedule
def add(a, b):
    return a+b

@schedule
def min(a, b):
    return a-b

@schedule
def mul(a, b):
    return a*b

@schedule
def sum(a):
    b = 1
    for i in a:
        b += i
    return b

# run example program
#---------------------
r1 = add(42, 43)
r2 = add(41, r1)
r3 = min(44, r1)
r4 = add(r2, r3)

# draw the execution graph
#-------------------------
draw_runner("graph1.svg", r4)

# a bit more complicated example
#-------------------------------
multiples = []
for i in range(10):
    diff = min(i, r2)
    multiples.append(mul(diff, r1))

# better:
# multiples = [mul(min(i, r2), r1) for i in range(10)]

r5 = sum(bind(*multiples))

draw_runner("graph2.svg", r5)

# Chemistry example
#------------------
@schedule
def ReadMolecule(smiles):
    pass

@schedule
def Optimize(settings, package, molecule):
    pass

@schedule
def Frequency(settings = None, package = None, molecule = None):
    pass
    
mollist = (ReadMolecule(m) for m in ['[OH2]', 'c1ccccc1', 'CCC'])

jobs=[]
for m in mollist:
    j =  Optimize({'basis' : 'DZP'}, 'adf', m)
    jobs.append(j)

tjobs=[]
for j in jobs:
    tjobs.append(Frequency(j, package='turbomole'))

draw_runner("graph-chem-1.svg", bind(*tjobs))

# alternative now

mollist = (ReadMolecule(m) for m in ['[OH2]', 'c1ccccc1', 'CCC'])

jobs=[Frequency(Optimize({'basis' : 'DZP'}, 'adf', m), package='turbomole')
    for m in mollist]

bind(*jobs).run()

#draw_runner("graph-chem-2.svg", bind(*jobs))



