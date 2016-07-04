Development documentation
=========================
.. automodule:: noodles
    :members: schedule, run_single, run_parallel, run_process, gather

Internal Specs
--------------
.. automodule:: noodles.workflow
    :members: from_call, NodeData, FunctionNode, Workflow

Promised object
---------------
.. automodule:: noodles.interface
    :members: PromisedObject

Runners
-------
.. automodule:: noodles.run.scheduler
    :members: Scheduler

.. automodule:: noodles.run.hybrid
    :members: hybrid_threaded_worker, run_hybrid

Serialisation
-------------
.. automodule:: noodles.serial
    :members: base, pickle, numpy

.. automodule:: noodles.serial.registry
    :members: Registry, Serialiser, RefObject

Worker executable
-----------------
.. automodule:: noodles.worker
