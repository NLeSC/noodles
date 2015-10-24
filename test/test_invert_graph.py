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
    
    C = get_workflow(C)
    A = get_workflow(A)
    B = get_workflow(B)
    
    assert is_workflow(C)
    assert C.nodes[C.top].bound_args.args == (Empty, Empty)
    assert (C.top, ArgumentAddress(ArgumentKind.regular, 'a', None)) in C.links[A.top]
    assert (C.top, ArgumentAddress(ArgumentKind.regular, 'b', None)) in C.links[B.top]
    
    deps = invert_links(C.links)
    assert deps == {A.top: {},
                     B.top: {},
                     C.top: {ArgumentAddress(ArgumentKind.regular, 'a', None): A.top,
                             ArgumentAddress(ArgumentKind.regular, 'b', None): B.top}}

def test_is_node_ready():
    A = value(1)
    B = add(1, A)
    A = get_workflow(A)
    B = get_workflow(B)

    assert is_node_ready(A.nodes[A.top])
    assert not is_node_ready(B.nodes[B.top])
    
