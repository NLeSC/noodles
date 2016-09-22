from collections import namedtuple
from noodles import serial
from noodles.serial.namedtuple import (SerNamedTuple)
from noodles.serial import (Registry)

A = namedtuple('A', ['x', 'y'])
B = namedtuple('B', ['u', 'v'])


def registry1():
    return Registry(
        parent=serial.base(),
        types={
            A: SerNamedTuple(A)
        })


def registry2():
    return serial.base() + serial.namedtuple()


def test_namedtuple_00():
    a = A(73, 38)
    r = registry1()
    assert r.deep_decode(r.deep_encode(a)) == a

    b = B(783, 837)
    r = registry2()
    print(r.deep_encode(b))
    assert r.deep_decode(r.deep_encode(b)) == b
