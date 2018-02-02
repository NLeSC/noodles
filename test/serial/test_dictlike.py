from noodles import serial
from noodles.serial.numpy import arrays_to_string


def registry():
    """Serialisation registry for matrix testing backends."""
    return serial.base() + arrays_to_string()


class A(dict):
    pass


def test_encode_dictlike():
    reg = registry()
    a = A()
    a['value'] = 42
    encoded = reg.deep_encode(a)
    decoded = reg.deep_decode(encoded, deref=True)
    assert isinstance(decoded, A)
    assert decoded['value'] == 42
    deref = reg.dereference(a)
    assert isinstance(decoded, A)
    assert decoded['value'] == 42
