.. Noodles documentation master file, created by
   sphinx-quickstart on Wed Nov 11 13:52:27 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Noodles's documentation!
===================================

Introduction
------------
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

Copyright & Licence
-------------------

Noodles 0.3.0 is copyright by the *Netherlands eScience Center (NLeSC)* and released under the Apache v2 License.

See http://www.esciencecenter.nl for more information on the NLeSC.

Installation
------------

.. WARNING:: We don't support Python versions lower than 3.5.

The core of Noodles runs on **Python 3.5** and above. To run Noodles on your own machine, no extra dependencies are required. It is advised to install Noodles in a virtualenv. If you want support for `Xenon`_, install `pyxenon`_ too.

.. code-block:: bash

    # create the virtualenv
    virtualenv -p python3 <venv-dir>
    . <venv-dir>/bin/activate

    # install noodles
    pip install noodles

Noodles has several optional dependencies. To be able to use the Xenon job scheduler, install Noodles with::

    pip install noodles[xenon]

The provenance/caching feature needs TinyDB installed::

    pip install noodles[prov]

To be able to run the unit tests::

    pip install noodles[test]

Documentation Contents
======================

.. toctree::
    :maxdepth: 2

    Introduction <self>
    eating
    cooking
    tutorials
    implementation


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Xenon: http://nlesc.github.io/Xenon/
.. _pyxenon: http://github.com/NLeSC/pyxenon
.. _`generating SSH keys`: https://help.github.com/articles/generating-ssh-keys/
.. _`decorators`: https://www.thecodeship.com/patterns/guide-to-python-function-decorators/
