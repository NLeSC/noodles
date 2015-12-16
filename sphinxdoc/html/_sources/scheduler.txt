.. highlight:: python
    :linenothreshold: 5

.. _noodles-scheduler:

The Noodles Scheduler
=====================

The Noodles scheduler is completely separated from the worker infrastructure. The scheduler accepts a single worker as an argument. This worker provides the scheduler with two coroutines. One acts as a generator of results, the other as a sink for jobs (the scheduler calls the ``send()`` method on it).

Both jobs and results are accompanied by a unique key to identify the associated job. The scheduler loops over the results as follows (more or less):

.. code-block:: python

    for (key, result) in source:
        """process result"""
        ...

        for node in workflow.nodes:
            if node.ready():
                sink.send((node.key, node.job))

Local workers
-------------

The single worker
~~~~~~~~~~~~~~~~~

It is the responsibility of the worker to keep a queue where so desired. A single result may trigger many new nodes to be ready for evaluation. This means that either the jobs or the results must be buffered in a queue. In the simplest case we have a single worker in the same thread as the scheduler.

.. figure:: _static/images/sd-single.svg
    :alt: sequence diagram, single thread
    :align: center

    Sequence diagram for a single threaded execution model.

The worker code looks like this:

::

    from noodles.coroutines import (IOQueue, Connection)
    from noodles.run_common import run_job

    def single_worker():
        """Sets up a single worker co-routine."""
        jobs = IOQueue()

        def get_result():
            source = jobs.source()

            for key, job in source:
                yield (key, run_job(job))

        return Connection(get_result, jobs.sink)

The ``IOQueue`` class wraps a standard Python queue. It provides a ``sink`` member pushing elements onto the queue, and a ``source`` member yielding elements from the queue, calling ``Queue.task_done()`` when the coroutine regains control.
The ``Connection`` class packs a coroutine source (a generator) and a sink. Together these objects provide a plug-board interface for the scheduler and a hierarchy of workers.

Now, when the scheduler calls ``sink.send(...)``, the job is pushed onto the queue that is created in ``single_worker()``. When the scheduler iterates over the results, ``get_result()`` feeds it results that it computes itself (through ``run_job``).

The Python queue is thread-safe. We may call ``jobs.source()`` in a different thread in another worker. This worker then safely pulls jobs from the same queue.

The Threaded worker
~~~~~~~~~~~~~~~~~~~

To have several workers run in tandem we need to keep a result queue in addition to the job queue. In the next sequence diagram we see how any number of threads are completely decoupled from the thread that manages the scheduling.

.. figure:: _static/images/sd-threaded.svg
    :alt: sequence diagram, multiple threads
    :align: center

    Sequence diagram where the actual job execution is deferred to one or more additional threads.

In Python source this looks as follows:

::

    def threaded_worker(n_threads):
        """Sets up a number of threads, each polling for jobs."""
        job_q = IOQueue()
        result_q = IOQueue()

        worker_connection = QueueConnection(job_q, result_q)
        scheduler_connection = QueueConnection(result_q, job_q)

        def worker(source, sink):
            for key, job in source:
                sink.send((key, run_job(job)))

        for i in range(n_threads):
            t = threading.Thread(
                target=worker,
                args=worker_connection.setup())

            t.daemon = True
            t.start()

        return scheduler_connection


The Hybrid worker
~~~~~~~~~~~~~~~~~

.. figure:: _static/images/sd-hybrid.svg
    :alt: sequence diagram, hybrid model
    :align: center

    Sequence diagram where the jobs get dispatched, each to a worker selected by a dispatcher.

Remote workers
--------------

Xenon
~~~~~

Fireworks
~~~~~~~~~
