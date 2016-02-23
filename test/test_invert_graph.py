from noodles import schedule
from noodles.workflow import (
    invert_links, get_workflow, is_workflow, Empty, ArgumentAddress,
    ArgumentKind, is_node_ready)


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
    assert C.nodes[C.root].bound_args.args == (Empty, Empty)
    assert (C.root, ArgumentAddress(ArgumentKind.regular, 'a', None)) \
        in C.links[A.root]
    assert (C.root, ArgumentAddress(ArgumentKind.regular, 'b', None)) \
        in C.links[B.root]

    deps = invert_links(C.links)
    assert deps == {
        A.root: {},
        B.root: {},
        C.root: {
            ArgumentAddress(ArgumentKind.regular, 'a', None): A.root,
            ArgumentAddress(ArgumentKind.regular, 'b', None): B.root}}


def test_is_node_ready():
    A = value(1)
    B = add(1, A)
    A = get_workflow(A)
    B = get_workflow(B)

    assert is_node_ready(A.nodes[A.root])
    assert not is_node_ready(B.nodes[B.root])
