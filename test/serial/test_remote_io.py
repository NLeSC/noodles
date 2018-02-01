"""
Testing JSON serialisation writer and reader.
"""

import io
import math

from noodles.run.remote.io import (JSONObjectReader, JSONObjectWriter)
from noodles.serial import base as registry


objects = ["Hello", 42, [3, 4], (5, 6), {"hello": "world"},
           math.tan, object]


def test_json():
    """Test streaming JSON objects."""
    f = io.StringIO()
    output_stream = JSONObjectWriter(registry(), f)

    for obj in objects:
        output_stream.send(obj)

    f.seek(0)
    input_stream = JSONObjectReader(registry(), f)

    new_objects = list(input_stream)

    assert new_objects == objects
