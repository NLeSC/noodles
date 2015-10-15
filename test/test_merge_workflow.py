from nose.tools import raises

from engine import *

def dummy(a, b, c, *args, **kwargs):
    pass
    
def test_is_workflow():
    assert is_workflow(Workflow(top=None, nodes={}, links={}))
    
def test_splice_list():
    odd = lambda x: x % 2 == 1
    assert splice_list(odd, range(6)) == ([0, Empty, 2, Empty, 4, Empty],
                                           [Empty, 1, Empty, 3, Empty, 5])

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
    assert C.nodes[C.top].args == [Empty, Empty]
    assert (C.top, ArgumentType.regular, 'a') in C.links[A.top]
    assert (C.top, ArgumentType.regular, 'b') in C.links[B.top]

def test_binder():
    A = value(1)
    B = value(2)
    C = bind(A, B)
    
    assert is_workflow(C)
    assert C.nodes[C.top].varargs == [Empty, Empty]
    assert (C.top, ArgumentType.variadic, 0) in C.links[A.top]
    assert (C.top, ArgumentType.variadic, 1) in C.links[B.top]

@schedule
def takes_keywords(s, **kwargs):
    pass

def test_with_keywords():
    A = value(1)
    B = value(2)
    C = takes_keywords(a = A, b = B, s = "regular!")
    
    assert is_workflow(C)
    assert C.nodes[C.top].args     == ["regular!"]
    assert C.nodes[C.top].varargs  == []
    assert C.nodes[C.top].keywords == {'a': Empty, 'b': Empty}
    assert (C.top, ArgumentType.keyword, 'a') in C.links[A.top]
    assert (C.top, ArgumentType.keyword, 'b') in C.links[B.top]

