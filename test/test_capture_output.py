from noodles import run_process, schedule

@schedule
def writes_to_stdout():
    print("Hello Noodles!")
    return 42

def test_capture_output():
    a = writes_to_stdout()
    result = run_process(a, n_processes=1)
    assert result == 42