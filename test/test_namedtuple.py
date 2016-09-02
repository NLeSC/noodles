from collections import namedtuple
from noodles.serial.namedtuple import SerNamedTuple
from noodles.serial import (Registry, base)

A = namedtuple('A', ['x', 'y'])


def registry():
    return Registry(
        parent=base(),
        types={
            A: SerNamedTuple(A)
        })


def test_namedtuple_00():
    a = A(73, 38)
    r = registry()
    assert r.deep_decode(r.deep_encode(a)) == a

