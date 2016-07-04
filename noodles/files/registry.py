from ..serial import (Registry)
from .path import (Path, SerPath)


def registry():
    return Registry(
        types={
            Path: SerPath()
        }
    )
