from nose.tools import raises

from engine import *

def dummy(a, b, c, *args, **kwargs):
    pass
    
def test_is_workflow():
    assert is_workflow(Workflow(top=None, nodes={}, links={}))
    
@schedule
def value(a):
    return a

@schedule
def add(a, b):
    return a+b
    
def test_merge_workflow():
    A = value(1)
    B = value(2)
    C = add(A, B)
    
    assert is_workflow(C)
    C = get_workflow(C)
    A = get_workflow(A)
    B = get_workflow(B)
    assert C.nodes[C.top].bound_args.args == (Empty, Empty)
    assert (C.top, ArgumentAddress(ArgumentKind.regular, 'a', None)) in C.links[A.top]
    assert (C.top, ArgumentAddress(ArgumentKind.regular, 'b', None)) in C.links[B.top]

def test_binder():
    A = value(1)
    B = value(2)
    C = bind(A, B)

    C = get_workflow(C)
    A = get_workflow(A)
    B = get_workflow(B)
    
    assert is_workflow(C)
    assert C.nodes[C.top].bound_args.args == (Empty, Empty)
    assert (C.top, ArgumentAddress(ArgumentKind.variadic, 'args', 0)) in C.links[A.top]
    assert (C.top, ArgumentAddress(ArgumentKind.variadic, 'args', 1)) in C.links[B.top]

@schedule
def takes_keywords(s, **kwargs):
    pass

def test_with_keywords():
    A = value(1)
    B = value(2)
    C = takes_keywords(a = A, b = B, s = "regular!")
    C = get_workflow(C)
    A = get_workflow(A)
    B = get_workflow(B)

    assert is_workflow(C)
    assert C.nodes[C.top].bound_args.args     == ("regular!",)
    assert C.nodes[C.top].bound_args.kwargs   == {'a': Empty, 'b': Empty}

