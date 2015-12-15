.. Noodles documentation master file, created by
   sphinx-quickstart on Wed Nov 11 13:52:27 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Noodles's documentation!
===================================

Contents:

.. toctree::
   :maxdepth: 2

Introduction
============
The primary goal of Noodles is to make it easy to run jobs on cluster supercomputers, in parallel, straight from a Python shell. The user enters a Python script that looks and feels like a serial program. The Noodles engine then converts this script into a call graph. This graph can be executed on a variety of machines using the different back-end runners that Noodles provides. This is not so much a design driven by technology but by social considerations.

Docs
====
.. automodule:: noodles
    :members: schedule, run, run_parallel, PromisedObject, gather

Internal Specs
==============
.. automodule:: noodles.datamodel
    :members: look_up, module_and_name, importable, from_call, Node, FunctionNode, Workflow

Promised object
---------------
.. automodule:: noodles.decorator
    :members: PromisedObject

Runners
=======
.. automodule:: noodles.coroutines
    :members: IOQueue, Connection, QueueConnection, patch

.. automodule:: noodles.run_common
    :members: run_job, Scheduler

.. automodule:: noodles.run_hybrid
    :members: hybrid_threaded_worker, run_hybrid

Worker executable
=================
.. automodule:: noodles.worker

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`