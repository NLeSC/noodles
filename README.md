# QM Works - workflow engine

Current requirements for running the prototype are:
*   Python 3
*   GraphViz
*   pygraphviz

## The prototype
The prototype is very simple. It should support the definition of function
objects that are manageble in the workflow engine and give output of the
workflow as a graph. The only dependency of this prototype should be the
graph plotting library: `pygraphviz`. To keep the interface clean, we avoid the
use of Fireworks specific functionality at this point. The abstract concepts
in this context are: workflow, node, link.

## Developers interface

Questions:
*   What does a developer adding functionality to the workflow engine need to 
    know?
*   How do we specify the surrounding context of functions in terms of types 
    and monadic context?

## User interface

The user should have it easy. From the spirit of wishful programming, we may 
give here some examples of how the user would use the workflow engine.

## Prototype example

The developer has prepared some nice functions for the user:

    @schedule
    def add(a, b):
        return a+b

    @schedule
    def min(a, b):
        return a-b

The user then uses these in a workflow:

    r1 = add(42, 43)
    r2 = add(41, r1)
    r3 = min(44, r1)
    r4 = add(r2, r3)

    compute(r4)