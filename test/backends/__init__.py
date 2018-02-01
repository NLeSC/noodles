"""
Defines backends for the test matrix.
"""

from noodles import run_single
from noodles import run_parallel
from noodles import run_process, serial
from noodles.run.single.sqlite3 import run_single as run_single_sqlite
from noodles.serial.numpy import arrays_to_string
from noodles.run.threading.sqlite3 import run_parallel as run_parallel_sqlite
from .backend_factory import backend_factory


def registry():
    """Serialisation registry for matrix testing backends."""
    return serial.pickle() + serial.base() + arrays_to_string()


backends = {
    'single': backend_factory(
        run_single, supports=['local']),
    'single-sqlite': backend_factory(
        run_single_sqlite, supports=['local', 'prov'],
        db_file=':memory:', registry=registry),
    'threads-4': backend_factory(
        run_parallel, supports=['local'], n_threads=4),
    'threads-4-sqlite': backend_factory(
        run_parallel_sqlite, supports=['local', 'prov'],
        n_threads=4, db_file=':memory:', registry=registry),
    'processes-2': backend_factory(
        run_process, supports=['remote'], n_processes=2, registry=registry,
        verbose=True),
    'processes-2-msgpack': backend_factory(
        run_process, supports=['remote'], n_processes=2, registry=registry,
        use_msgpack=True)
}

__all__ = ['backends']
