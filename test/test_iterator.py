import noodles
import nose


@nose.tools.raises(TypeError)
def test_iterate():
    a = noodles.delay((1,2,3))
    b, c, d = a
    e = noodles.gather(d, c, b)

    result = noodles.run_single(e)
    assert result == (3, 2, 1)
