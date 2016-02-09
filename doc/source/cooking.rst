Cooking of Noodles (library docs)
=================================

The cooking of good Noodles can be tricky. We try to make it as easy as possible, but to write good Noodles you need to settle in a *functional style* of programming. The functions you design cannot write to some global state, or modify its arguments and expect these modifications to persist throughout the program. This is not a restriction of Noodles itself, this is a fundamental principle that applies to all possible frameworks for parallel and distributed programming. So get used to it!

Every function call in Noodles (that is, calls to scheduled function) can be visualised as a node in a call graph. You should be able to draw this graph conceptually when designing the program. Luckily there is (almost) always a way to write down non-functional code in a functional way.

.. NOTE:: Golden Rule 1: if you modify something, return it.

Call by value
-------------

Suppose we have the following program

::

    from noodles import (schedule, run_single)

    @schedule
    def double(x):
        return x['value'] * 2

    @schedule
    def add(x, y):
        return x + y

    a = {'value': 4}
    b = double(a)
    a['value'] = 5
    c = double(a)
    d = add(b, c)

    print(run_single(d))

If this were undecorated Python, the answer would be 18. However, the computation of this answer depends on the time-dependency of the Python interpreter. In Python, dictionaries are passed by reference. The promised object `b` then contains a reference to the dictionary in `a`. If we then change the value in this dictionary, the call producing the value of `b` is retroactively changed to double the value 5 instead of 4.

If Noodles is to evaluate this program correctly it needs to :py:func:`deepcopy` every argument to a scheduled function. There is an other way to have the same semantics produce a correct result. This is by making `a` a promised object in the first place. The third solution is to teach your user *functional programming*.
Deep copying function arguments can result in a significant performance penalty on the side of the job scheduler. In most applications that we target this is not the bottle neck.


Monads (sort of)
----------------

We still have ways to do object oriented programming and assignments. The :py:class:`PromisedObject` class has several magic methods overloaded to translate to functional equivalents.

Member assignment
~~~~~~~~~~~~~~~~~

Especially member assignment is treated in a particular way. Suppose ``a`` is a :py:class:`PromisedObject`, then the statement

::

    a.b = 3

is (conceptually) transformed into

::

    a = _setattr(a, 'b', 3)

where :py:func:`_setattr` is a scheduled function. The :py:class:`PromisedObject` contains a representation of the complete workflow representing the computation to get to the value of ``a``. In member assignment, this workflow is replaced with the new workflow containing this last instruction.

This is not a recommended way of programming. Every assignment results in a nested function call. The `statefulness` of the program is then implemented in the composition of functions, similar to how other functional languages do it using `monads`. It results in sequential code that will not parallelise so well.

Other magic methods
~~~~~~~~~~~~~~~~~~~



``Storable``
------------



Serialisation
-------------
