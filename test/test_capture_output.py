import pytest

from noodles import run_process, schedule, serial

try:
    import msgpack  # noqa
    has_msgpack = True
except ImportError:
    has_msgpack = False

@schedule
def writes_to_stdout():
    print("Hello Noodles!")
    return 42

@pytest.mark.skipif(not has_msgpack, reason="msgpack needed.")
def test_capture_output():
    a = writes_to_stdout()
    result = run_process(a, n_processes=1, registry=serial.base, use_msgpack=True)
    assert result == 42

def test_capture_output_nomsgpack():
    a = writes_to_stdout()
    result = run_process(a, n_processes=1, registry=serial.base, use_msgpack=False)
    assert result == 42
