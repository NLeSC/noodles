import pytest

try:
    from noodles.prov import prov_key
    from noodles.run.run_with_prov import (
        run_single, run_parallel, run_parallel_opt)
except ImportError:
    has_prov = False
else:
    has_prov = True

from noodles import serial, gather, schedule_hint
from noodles.tutorial import (add, mul, sub, accumulate)

from noodles.run.worker import run_job
from noodles.run.job_keeper import JobKeeper

import os


@schedule_hint(store=True)
def add2(x, y):
    return x + y


@schedule_hint(store=True)
def fib(n):
    if n < 2:
        return 1
    else:
        return add(fib(n - 1), fib(n - 2))


@pytest.mark.skipif(not has_prov, reason="TinyDB needed")
class TestProv:
    def test_prov_00(self):
        reg = serial.base()
        a = add(3, 4)
        b = sub(3, 4)
        c = add(3, 4)
        d = add(4, 3)

        enc = [reg.deep_encode(x._workflow.root_node) for x in [a, b, c, d]]
        key = [prov_key(o) for o in enc]
        assert key[0] == key[2]
        assert key[1] != key[0]
        assert key[3] != key[0]

    def test_prov_01(self):
        reg = serial.base()
        a = add(3, 4)

        enc = reg.deep_encode(a._workflow.root_node)
        dec = reg.deep_decode(enc)

        result = run_job(0, dec)
        assert result.value == 7

    def test_prov_02(self):
        db_file = "prov1.json"

        A = add(1, 1)
        B = sub(3, A)

        multiples = [mul(add(i, B), A) for i in range(6)]
        C = accumulate(gather(*multiples))

        result = run_single(C, serial.base, db_file)
        assert result == 42
        os.unlink(db_file)

    def test_prov_03(self):
        db_file = "prov2.json"

        A = add(1, 1)
        B = sub(3, A)

        multiples = [mul(add(i, B), A) for i in range(6)]
        C = accumulate(gather(*multiples))

        result = run_parallel(C, 4, serial.base, db_file, JobKeeper(keep=True))
        assert result == 42
        os.unlink(db_file)

    def test_prov_04(self):
        db_file = "prov3.json"

        A = add2(1, 1)
        B = sub(3, A)

        multiples = [mul(add2(i, B), A) for i in range(6)]
        C = accumulate(gather(*multiples))

        result = run_parallel_opt(C, 4, serial.base, db_file)
        assert result == 42
        os.unlink(db_file)

    def test_prov_05(self):
        import time
        db_file = "testjobs.json"

        wf = fib(20)
        start = time.time()
        result = run_parallel(wf, 4, serial.base, db_file)
        end = time.time()

        assert (end - start) < 5.0  # weak test
        assert result == 10946

        os.unlink(db_file)
