|rtfd| |travis| |zenodo| |codecov|

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

Install the latest version from PyPI:

.. code:: bash

    pip install noodles

Or, if you clone this repository,

.. code:: bash

    git clone git@github.com:NLeSC/noodles.git
    cd noodles
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
    tox

Some tests depend on the optional modules being installed. Those are skipped if
if imports fail. If you want to test everything, make sure you have NumPy
installed as well.

Documentation
-------------

All the latest documentation is available on `Read the Docs <https://noodles.rtfd.io/>`_.

.. |travis| image:: https://travis-ci.org/NLeSC/noodles.svg?branch=master
  :target: https://travis-ci.org/NLeSC/noodles
  :alt: Travis
.. |zenodo| image:: https://zenodo.org/badge/45391130.svg
  :target: https://zenodo.org/badge/latestdoi/45391130
  :alt: DOI
.. |codecov| image:: https://codecov.io/gh/NLeSC/noodles/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/NLeSC/noodles
.. |rtfd| image:: https://readthedocs.org/projects/noodles/badge/?version=latest
  :target: https://noodles.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status
