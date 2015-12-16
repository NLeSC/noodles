Noodles - workflow engine
=============================

Requirements for running the first release (0.1.0) are:

-   Python 3.5
-   xenon (packaged with pyxenon)
-   pyxenon

Installing
----------

To run the unittests, install the following in a virtualenv:

.. code:: bash

    # pyxenon needs jnius, which needs this env
    export JAVA_HOME="/usr/lib/jvm/default-java"  # or similar...
    pyvenv-3.5 <venv-dir>
    . <venv-dir>/bin/activate
    cd ../pyxenon          # git pull git@github.com:NLeSC/pyxenon.git
    make install
    cd ../noodles
    pip install .

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
