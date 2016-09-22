.. Noodles documentation master file, created by
   sphinx-quickstart on Wed Nov 11 13:52:27 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Noodles's documentation!
===================================

Introduction
------------
Noodles offers a model for parallel programming in Python. It can be used for a variety of tasks including data pipelines, and computational workflows. 

The primary goal of Noodles is to make it easy to run jobs on cluster supercomputers, in parallel, straight from a Python shell. The user enters a Python script that looks and feels like a serial program. The Noodles engine then converts this script into a call graph. This graph can be executed on a variety of machines using the different back-end runners that Noodles provides. This is not so much a design driven by technology but by social considerations. The end user may expect an elegant, easy to understand, interface to a computational library. This user experience we refer to as *eating of noodles*.

The computational library that is exposed to the user by means of Noodles needs to adhere to some design principles that are more strict than plain Python gives us. The library should follow a functional style of programming and is limited by the fact that function arguments need to pass through a layer where data is converted to and from a JSON format. The design of such a library is the *cooking of noodles*. As it is with ramen noodles, ofttimes the cook is also an avid consumer of noodles.

The complexity of running a workflow in parallel on a wide variety of architectures is taken care of by the Noodles engine. This is the *production of noodles* which is left as an exercise for the Noodles dev-team at the Netherlands eScience Center.

Copyright & Licence
-------------------

Noodles 0.1.0 is copyright by the *Netherlands eScience Center (NLeSC)* and released under the `LGPLv3`_.

See http://www.esciencecenter.nl for more information on the NLeSC.

Installation
------------

.. WARNING:: We don't support Python versions lower than 3.5.

The core of Noodles runs on **Python 3.5**. To run Noodles on your own machine, no extra dependencies are required. It is advised to install Noodles in a virtualenv. If you want support for `Xenon`_, install `pyxenon`_ too.

.. code-block:: bash

    # pyxenon needs Java, which may need JAVA_HOME to be set, put it in .bashrc
    export JAVA_HOME="/usr/lib/jvm/default-java"  # or similar...

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
   first_steps
   poetry_tutorial
   boil_tutorial
   development
   scheduler
   brokers

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Xenon: http://nlesc.github.io/Xenon/
.. _pyxenon: http://github.com/NLeSC/pyxenon
.. _LGPLv3: http://www.gnu.org/licenses/lgpl-3.0.html
.. _`generating SSH keys`: https://help.github.com/articles/generating-ssh-keys/
