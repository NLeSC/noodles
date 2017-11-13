from noodles.prov.workflow import (set_global_provenance)
from noodles.tutorial import (add, sub, mul)
from noodles.serial import base


def test_global_prov():
    a = add(4, 5)
    b = sub(a, 3)
    c = mul(b, 7)
    d = mul(b, 7)
    e = sub(c, 3)
    f = sub(c, 5)

    set_global_provenance(c._workflow, base())

    assert c._workflow.prov is not None
    assert b._workflow.prov is not None
    assert c._workflow.prov != b._workflow.prov

    set_global_provenance(d._workflow, base())
    set_global_provenance(e._workflow, base())
    set_global_provenance(f._workflow, base())

    assert c._workflow.prov == d._workflow.prov
    assert b._workflow.prov != e._workflow.prov
    assert f._workflow.prov != e._workflow.prov
