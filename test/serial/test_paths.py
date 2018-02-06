from pathlib import Path
from noodles import (serial)


def test_path():
    a = Path("/usr/bin/python")
    registry = serial.base()

    encoded = registry.deep_encode(a)
    b = registry.deep_decode(encoded)

    assert a == b
