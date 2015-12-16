Development documentation
=========================
.. automodule:: noodles
    :members: schedule, run, run_parallel, gather

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
.. automodule:: noodles.coroutines
    :members: IOQueue, Connection, QueueConnection, patch

.. automodule:: noodles.run_common
    :members: run_job, Scheduler

.. automodule:: noodles.run_hybrid
    :members: hybrid_threaded_worker, run_hybrid

Worker executable
-----------------
.. automodule:: noodles.worker
