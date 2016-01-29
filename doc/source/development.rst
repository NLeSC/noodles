Development documentation
=========================
.. automodule:: noodles
    :members: schedule, run_single, run_parallel, run_process, gather

Internal Specs
--------------
.. automodule:: noodles.datamodel
    :members: from_call, Node, FunctionNode, Workflow

Promised object
---------------
.. automodule:: noodles.decorator
    :members: PromisedObject

Runners
-------
.. automodule:: noodles.run.coroutines
    :members: IOQueue, Connection, QueueConnection, patch

.. automodule:: noodles.run.scheduler
    :members: run_job, Scheduler

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
