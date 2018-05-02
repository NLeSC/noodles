"""
(stub)

Noodles
=======
"""

from noodles.interface import (
    delay, gather, lift, schedule, schedule_hint, unwrap,
    has_scheduled_methods, update_hints, unpack, quote, unquote,
    gather_dict, result, gather_all, maybe, Fail, simple_lift, ref, failed)

from noodles.workflow import (get_workflow)
from .patterns import (fold, find_first, conditional)
from .run.runners import run_parallel_with_display as run_logging

from .run.threading.vanilla import run_parallel
from .run.single.vanilla import run_single

from .run.process import run_process
from .run.scheduler import Scheduler

__version__ = "0.3.0"

__all__ = ['schedule', 'schedule_hint', 'run_single', 'run_process',
           'Scheduler', 'has_scheduled_methods',
           'Fail', 'failed',
           'run_logging', 'run_parallel', 'unwrap', 'get_workflow',
           'gather', 'gather_all', 'gather_dict', 'lift', 'unpack',
           'maybe', 'delay', 'update_hints',
           'quote', 'unquote', 'result', 'fold', 'find_first',
           'conditional',
           'simple_lift', 'ref']
