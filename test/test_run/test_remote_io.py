from nose.plugins.skip import SkipTest
import io

from noodles.run.remote.io import (
    MsgPackObjectReader, MsgPackObjectWriter,
    JSONObjectReader, JSONObjectWriter)
from noodles.serial import base as registry
import math

try:
    import msgpack
    has_msgpack = True
except ImportError:
    has_msgpack = False


objects = ["Hello", 42, [3, 4], (5, 6), {"hello": "world"}, 
           math.tan, object]

        
def test_msgpack():
    if not has_msgpack:
        raise SkipTest("No MsgPack installed.")
    
    f = io.BytesIO()
    output_stream = MsgPackObjectWriter(registry(), f)
    
    for obj in objects:
        output_stream.send(obj)

    f.seek(0)
    input_stream = MsgPackObjectReader(registry(), f)
    
    new_objects = list(input_stream)
    assert new_objects == objects
    

def test_json():    
    f = io.StringIO()
    output_stream = JSONObjectWriter(registry(), f)
    
    for obj in objects:
        output_stream.send(obj)

    f.seek(0)
    input_stream = JSONObjectReader(registry(), f)
    
    new_objects = list(input_stream)
    
    assert new_objects == objects

