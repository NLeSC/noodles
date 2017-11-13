.. image:: https://travis-ci.org/NLeSC/noodles.svg?branch=master
   :alt: Travis
.. image:: https://api.codacy.com/project/badge/Grade/f45b3299dbb74ccb8f766701563a88db
   :target: https://www.codacy.com/app/Noodles/noodles?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=NLeSC/noodles&amp;utm_campaign=Badge_Grade
   :alt: Codacy Badge
.. image:: https://zenodo.org/badge/45391130.svg
   :target: https://zenodo.org/badge/latestdoi/45391130
   :alt: DOI
.. image:: https://api.codacy.com/project/badge/Coverage/f45b3299dbb74ccb8f766701563a88db
   :target: https://www.codacy.com/app/Noodles/noodles?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=NLeSC/noodles&amp;utm_campaign=Badge_Coverage
   :alt: Coverage Badge

Noodles - workflow engine
=========================

Requires Python 3.5. See http://nlesc.github.io/noodles/ for
more information.

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
