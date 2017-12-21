from noodles.lib import (object_name, look_up, importable)
import math
from pytest import raises


def test_object_name():
    assert object_name(math.sin) == 'math.sin'
    assert object_name(object_name) == 'noodles.lib.utility.object_name'

    with raises(AttributeError):
        object_name(1)


def test_look_up():
    from pathlib import Path
    assert look_up('math.sin') is math.sin
    assert look_up('pathlib.Path') is Path


def test_importable():
    import os
    assert not importable(3)
    assert importable(math.cos)
    assert not importable(lambda x: x*x)
    assert importable(importable)
    assert importable(raises)
    assert not importable(os.name)
