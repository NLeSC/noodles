Cooking of Noodles (library docs)
=================================

The cooking of good Noodles can be tricky. We try to make it as easy as possible, but to write good Noodles you need to settle in a *functional style* of programming. The functions you design cannot write to some global state, or modify its arguments and expect these modifications to persist throughout the program. This is not a restriction of Noodles itself, this is a fundamental principle that applies to all possible frameworks for parallel and distributed programming. So get used to it!

Every function call in Noodles (that is, calls to scheduled function) can be visualised as a node in a call graph. You should be able to draw this graph conceptually when designing the program. Luckily there is (almost) always a way to write down non-functional code in a functional way.

.. NOTE:: Golden Rule 1: if you modify something, return it.

Monads (sort of)
----------------

We still have ways to do object oriented programming and assignments. The :py:class:`PromisedObject` class has several magic methods overloaded to translate to functional equivalents.

Member assignment
~~~~~~~~~~~~~~~~~

Especially member assignment is treated in a particular way. Suppose ``a`` is a :py:class:`PromisedObject`, then the statement

..

    a.b = 3

is (conceptually) transformed into

..

    a = _setattr(a, 'b', 3)

The :py:class:`PromisedObject` contains a representation of the complete workflow representing the computation to get to the value of ``a``. In member assignment, this workflow is replaced with the new workflow containing this last instruction.

This is not a recommended way of programming. Every assignment results in a nested function call. The `statefulness` of the program is then implemented in the composition of functions, similar to how other functional languages do it using `monads`. It results in sequential code that will not parallelise so well.

Other magic methods
~~~~~~~~~~~~~~~~~~~



``Storable``
------------



Serialisation
-------------

