from noodles import schedule, run_process

@schedule
def init():
    global s
    s = "This global variable needs to be here!"
    return True


@schedule
def finish():
    return "Finish functino was run!"


@schedule
def checker():
    return s == "This global variable needs to be here!"


def test_globals():
    a = checker()
    result = run_process(a, n_processes=1, init=init, finish=finish)
    assert result

