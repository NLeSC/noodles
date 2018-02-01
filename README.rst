|travis| |zenodo| |codecov|

Noodles - easy parallel programming for Python
==============================================

Often, a computer program can be sped up by executing parts of its code *in
parallel* (simultaneously), as opposed to *synchronously* (one part after
another).

A simple example may be where you assign two variables, as follows ``a = 2 * i``
and ``b = 3 * i``. Either statement is only dependent on ``i``, but whether you
assign ``a`` before ``b`` or vice versa, does not matter for how your program
works. Whenever this is the case, there is potential to speed up a program,
because the assignment of ``a`` and ``b`` could be done in parallel, using
multiple cores on your computer's CPU. Obviously, for simple assignments like
``a = 2 * i``, there is not much time to be gained, but what if ``a`` is the
result of a time-consuming function, e.g. ``a = very_difficult_function(i)``?
And what if your program makes many calls to that function, e.g. ``list_of_a =
[very_difficult_function(i) for i in list_of_i]``? The potential speed-up could
be tremendous.

So, parallel execution of computer programs is great for improving performance,
but how do you tell the computer which parts should be executed in parallel, and
which parts should be executed synchronously? How do you identify the order in
which to execute each part, since the optimal order may be different from the
order in which the parts appear in your program. These questions quickly become
nearly impossible to answer as your program grows and changes during
development. Because of this, many developers accept the slow execution of their
program only because it saves them from the headaches associated with keeping
track of which parts of their program depend on which other parts.

Enter Noodles.

Noodles is a Python package that can automatically construct a *callgraph*
for a given Python program, listing exactly which parts depend on which parts.
Moreover, Noodles can subsequently use the callgraph to execute code in parallel
on your local machine using multiple cores. If you so choose, you can even
configure Noodles such that it will execute the code remotely, for example on a
big compute node in a cluster computer.

Installation
------------
Install the following in a virtualenv:

.. code:: bash

    pip install .

To enable Xenon for remote execution, Java must be installed, and Xenon
can be installed with

.. code:: bash

    pip install '.[xenon]'

If Java cannot be found (needed by Xenon), run

.. code:: bash

    export JAVA_HOME="/usr/lib/jvm/default-java"  # or similar...

in your shell initialization script (like `~/.bashrc`).

To enable the TinyDB based job database, run

.. code:: bash

    pip install '.[prov]'

This is needed if you want to interrupt a running workflow and resume where
you left of, or to reuse results over multiple runs.

To run unit tests, run

.. code:: bash

    pip install '.[test]'
    nosetests test

Some tests depend on the optional modules being installed. Those are skipped if
if imports fail. If you want to test everything, make sure you have NumPy
installed as well.

The prototype
-------------
The prototype is very simple. It should support the definition of function
objects that are manageable in the workflow engine and give output of the
workflow as a graph. The only dependency of this prototype should be the
graph plotting library: `pygraphviz`. To keep the interface clean, we avoid the
use of Fireworks specific functionality at this point. The abstract concepts
in this context are: workflow, node, link.

Developers interface
--------------------
Questions:

-   What does a developer adding functionality to the workflow engine need to
    know?
-   How do we specify the surrounding context of functions in terms of types
    and monadic context?

User interface
--------------
The user should have it easy. From the spirit of wishful programming, we may
give here some examples of how the user would use the workflow engine.

Prototype example
-----------------
The developer has prepared some nice functions for the user:

.. code:: python

    @schedule
    def f(a, b):
        return a+b

    @schedule
    def g(a, b):
        return a-b

    @schedule
    def h(a, b):
        return a*b

The user then uses these in a workflow:

.. code:: python

    u = f(5, 4)
    v = g(u, 3)
    w = g(u, 2)
    x = h(v, w)

    draw_graph("graph-example1.svg", x)

Resulting in the graph:

.. image:: examples/callgraph.png?raw=true

.. |travis| image:: https://travis-ci.org/NLeSC/noodles.svg?branch=master
  :target: https://travis-ci.org/NLeSC/noodles
  :alt: Travis
.. |zenodo| image:: https://zenodo.org/badge/45391130.svg
  :target: https://zenodo.org/badge/latestdoi/45391130
  :alt: DOI
.. |codecov| image:: https://codecov.io/gh/NLeSC/noodles/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/NLeSC/noodles
