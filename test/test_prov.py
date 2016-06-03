from noodles.prov import prov_key
from noodles import serial
from noodles.tutorial import add, sub, mul
from noodles.prov import prov_key

import json

def test_prov_00():
    reg = serial.base()
    a = add(3, 4)
    b = sub(3, 4)
    c = add(3, 4)
    d = add(4, 3)
 
    enc = [reg.deep_encode(x._workflow.root_node) for x in [a, b, c, d]]
    key = [prov_key(o) for o in enc]
    assert key[0] == key[2]
    assert key[1] != key[0]
    assert key[3] != key[0]

