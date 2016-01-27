from noodles.utility import deep_map


class A:
    def __init__(self, value):
        self.value = value


class B(A):
    pass


def translate(a):
    if isinstance(a, A):
        name = type(a).__name__
        return {'type': name, 'value': a.value}

    else:
        return a


def test_deep_map():
    a = A(5)
    b = A("Hello")
    c = B(67.372)
    d = B([a, b])
    e = A({'one': c, 'two': d})

    result = deep_map(translate, e)
    print(result)
    assert result['value']['two']['value'][0]['value'] == 5
    assert result['value']['one']['type'] == 'B'
    assert result['value']['two']['value'][1]['value'] == "Hello"

