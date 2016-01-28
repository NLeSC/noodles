from noodles import run_process, schedule, serial

class A(dict):
    pass

@schedule
def f(a):
    a['value'] = 5
    return a

def test_dict_like():
    a = A()
    b = f(a)
    result = run_process(b, 1, serial.base)

    assert isinstance(result, A)
    assert result['value'] == 5
