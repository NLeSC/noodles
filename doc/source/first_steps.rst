First Steps 
===========

**This tutorial is also available in the form of a Jupyter Notebook. Try it out, and play!**

Noodles is there to make your life easier, *in parallel*! The reason why Noodles can be easy and do parallel Python at the same time is its *functional* approach. In one part you'll define a set of functions that you'd like to run with Noodles, in an other part you'll compose these functions into a *workflow graph*. To make this approach work a function should not have any *side effects*. Let's not linger and just start noodling! First we define some functions to use.


.. code:: python

    from noodles import schedule
    
    @schedule
    def add(x, y):
        return x + y
    
    @schedule
    def mul(x,y):
        return x * y

Now we can create a workflow composing several calls to this function.

.. code:: python

    a = add(1, 1)
    b = mul(a, 2)
    c = add(a, a)
    d = mul(b, c)

That looks easy enough; the funny thing is though, that nothing has been computed yet! Noodles just created the workflow graphs corresponding to the values that still need to be computed. Until such time, we work with the *promise* of a future value. Using the module ``pygraphviz`` (`pip install pygraphviz`, check `this post <https://stackoverflow.com/questions/40528048/pip-install-pygraphviz-no-package-libcgraph-found>`_ if you have problems installing pygraphviz) we can look at the call graphs.

.. code:: python

    from draw_workflow import draw_workflow
    import sys
    import os
    
    draw_workflow("wf1a.png", a._workflow)
    draw_workflow("wf1b.png", b._workflow)
    draw_workflow("wf1c.png", c._workflow)
    draw_workflow("wf1d.png", d._workflow)
    
    err = os.system("montage wf1?.png -tile 4x1 -geometry +10+0 wf1-series.png")

``draw_workflow`` imports ``pygraphviz``. ``wf1-series.png`` is saved to the directory from which you launched this notebook.

.. figure:: _static/images/wf1-series.png
    :alt: building the workflow
    :align: center
    :figwidth: 100%

Now, to compute the result we have to tell Noodles to evaluate the program.

.. code:: python

    from noodles import run_parallel, run_single
    
    run_parallel(d, n_threads=2)




.. parsed-literal::

    16

