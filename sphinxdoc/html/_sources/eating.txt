.. highlight:: python
    :linenothreshold: 5

Eating of Noodles (user docs)
=============================

The purpose of Noodles is to make it easy to design *computational workflows* straight from Python. Noodles is meant to be used by scientists that want to do heavy number crunching, and need a way to organise these computations in a readable and sustainable manner. These workflows are usually associated with a *directed acyclic graph* (DAG, or just: graph). Each computation in the workflow is a represented as a node in the graph and may have several dependencies. These dependencies are the arrows; or if you think in reverse, the arrows show transport of data.

A first example
---------------

Let's look at a small example creating a diamond workflow. All the examples in this documentation do some silly arithmetic. In practice these functions would do quite a bit heavier lifting.

::

    from noodles import run
    from noodles.tutorial import (add, sub, mul)

    u = add(5, 4)
    v = sub(u, 3)
    w = sub(u, 2)
    x = mul(v, w)

    answer = run(x)

    print("The answer is {0}.".format(answer))

That allmost looks like normal Python! The only difference is the ``run`` statement at the end of this program. The catch is that none of the computation is actually done until the ``run`` statement has been given. The variables ``u``, ``v``, ``w``, and ``x`` only represent the *promise* of a value. The functions that we imported are wrapped, such that they construct the directed acyclic graph of the computation in stead of just computing the result immediately. This DAG then looks like this:

.. figure:: _static/images/dag1.png
    :alt: the diamond workflow DAG
    :align: center
    :figwidth: 50%

    The diamond workflow.

Running this program will first evaluate the result to ``add(5, 4)``. The resulting value is than inserted into the empty slots in the depending nodes. Each time a node has no empty slots left, it is scheduled for evaluation. At the end, the program should print:

::

    The answer is 42.

At this point it is good to know what the module ``noodles.tutorial`` looks like. It looks very simple. However, a user should be aware of what happens behind the curtains, to understand the limitations of this approach.

::

    from noodles import schedule

    @schedule
    def add(a, b):
      """Adding up numbers! (is very uplifting)"""
      return a + b

    @schedule
    def sub(a, b):
      """Subtracting numbers."""
      return a - b

    @schedule
    def mul(a, b):
      """Multiplying numbers."""
      return a * b

    ...

The ``@schedule`` decorators take care that the functions actually return *promises* in stead of values. Such a ``PromisedObject`` is a placeholder for the expected result. It stores the workflow graph that is needed to compute the promise. When another `schedule`-decorated function is called with a promise, the graphs of the dependencies are merged to create a new workflow graph.

Doing things parallel
~~~~~~~~~~~~~~~~~~~~~

Using the Noodles approach it becomes very easy to paralellise computations. Let's look at a second example.

::

    from noodles import (gather, run_parallel)
    from noodles.tutorial import (add, sub, mul, accumulate)


    def my_func(a, b, c):
        d = add(a, b)
        return mul(d, c)


    u = add(1, 1)
    v = sub(3, u)
    w = [my_func(i, v, u) for i in range(6)]
    x = accumulate(gather(*w))

    answer = run_parallel(r5, n_threads=4)

    print("The answer is ${0}, again.".format(answer))

This time the workflow graph will look a bit more complicated.

.. figure:: _static/images/dag2.png
    :alt: the workflow graph of the second example
    :align: center
    :figwidth: 100%

    The workflow graph of the second example.

Here we see how a user can define normal python functions and use them to build a larger workflow. Furthermore, we introduce a new bit of magic: the ``gather`` function. The user builds a list of computations using a list-comprehension and storing a *list of promises* in variable ``w``. Schedule-decorated function need to know what arguments contain promised values and what arguments are plain Python. What ``gather`` does, is to convert the list of promises into a promise of a list. It is defined as follows:

::

    @schedule
    def gather(*lst):
        return lst

By unpacking the list (we do ``gather(*w)``) in the call to gather, each item in ``w`` becomes a dependency of the ``gather`` node in this workflow, as we can see in the figure above.

To make use of the parallelism present in this workflow, we run in with ``run_parallel``. This runner function creates a specified number of threads, each taking jobs from the Noodles scheduler and returning results.

Running workflows
-----------------

Noodles ships with a few ready-made functions that run the workflow for you, depending on the amount of work that needs to be done.

``run``, local single thread
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Runs your workflow in the same thread as the caller. Why are you using Noodles and not a parallel runner? This function is mainly for testing.

``run_parallel``, local multi-thread
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Runs your workflow in parallel using any number of threads. Usually, specifying the number of cores in your CPU will give optimal performance for this runner.

.. NOTE:: If you are very **very** certain that your workflow will never need to scale to cluster-computing, this runner is more lenient on the kinds of Python that is supported, because function arguments are not converted to and from JSON. Think of nested functions, lambda forms, generators, etc.

``run_process``, local multi-process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Starts a second process to run jobs. This is usefull for testing the JSON compatability of your workflow on your own machine.

Xenon
~~~~~
Xenon_ is a Java library offering a uniform interface to all manners of job schedulers. Running a job on your local machine is as easy as submitting it to SLURM or Torque on your groceries supercomputer. To talk to Xenon from Python we use pyxenon_.

Using the Xenon runner, there are two modes of operation: *batch* and *online*. In online mode, jobs are streamed to the worker and results read back. If your laptop crashes while an online computation is running, that is to say, the connection is broken, the worker dies and you may lose results. Getting the online mode to be more robust is one of the aims for upcomming releases.

Fireworks
~~~~~~~~~
Fireworks_ is a workflow engine that runs workflows as stored in a MongoDB. This is the `Dicke Bertha`_ in our armoury. Fireworks support is still in an early stage of development. The advantage of Fireworks is that it is here, it works and it is robust. However, it may be a hassle with the system admins to setup a MongoDB and be allowed to communicate with it from within the cluster environment.

Hybrid mode
~~~~~~~~~~~
We may have a situation where a workflow consists of some very heavy *compute* jobs and a lot of smaller jobs that do some bookkeeping. If we were to schedule all the menial jobs to a SLURM queue we actually slow down the computation through the overhead of job submission. The Noodles cook may provide the schedule functions with hints on the type of job the function represents. Depending on these hints we may dispatch the job to a remote worker or keep it on the local machine.

We provide an example on how to use the hybrid worker in the source.

If you really need to, it is not too complicated to develop your own job runner based on some of these examples. Elsewhere in this documentation we elaborate on the architecture and interaction between runners and the scheduler, see: :ref:`noodles-scheduler`.

.. _Fireworks: https://pythonhosted.org/FireWorks/index.html
.. _Dicke Bertha: https://en.wikipedia.org/wiki/Big_Bertha_%28howitzer%29
.. _Xenon: http://nlesc.github.io/Xenon/
.. _pyxenon: http://github.com/NLeSC/pyxenon
