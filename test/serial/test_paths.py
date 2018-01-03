from noodles import (serial, files)


def test_path():
    a = files.Path("/usr/bin/python")
    registry = serial.base() + files.registry()

    encoded = registry.deep_encode(a)
    b = registry.deep_decode(encoded)

    assert a.path == b.path
