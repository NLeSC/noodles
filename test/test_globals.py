"""
Test the use of init and finish functions.
"""

from noodles import schedule, run_process, serial


def init():
    """Creates a global variable ``s``, and returns True."""
    global S
    S = "This global variable needs to be here!"
    return True


def finish():
    """Just print a message."""
    return "Finish functino was run!"


@schedule
def checker():
    """Check if global variable ``s`` exists."""
    return S == "This global variable needs to be here!"


def test_globals():
    """Test init and finish functions on ``run_process``."""
    a = checker()
    result = run_process(a, n_processes=1, registry=serial.base,
                         init=init, finish=finish)
    assert result
