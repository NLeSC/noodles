from engine import *

@schedule
def value(a):
    return a

@schedule
def add(a, b):
    return a+b
    
def test_invert_links():
    A = value(1)
    B = value(2)
    C = add(A, B)
    
    assert is_workflow(C)
    assert C.nodes[C.top].args == [Empty, Empty]
    assert (C.top, ArgumentType.regular, 'a') in C.links[A.top]
    assert (C.top, ArgumentType.regular, 'b') in C.links[B.top]
    
    deps = invert_links(C.links)
    assert deps == {A.top: {},
                     B.top: {},
                     C.top: {(ArgumentType.regular, 'a'): A.top,
                             (ArgumentType.regular, 'b'): B.top}}

def test_is_node_ready():
    A = value(1)
    B = add(1, A)
    assert is_node_ready(A.nodes[A.top])
    assert not is_node_ready(B.nodes[B.top])
    
