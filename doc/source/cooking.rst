Cooking of Noodles (library docs)
=================================

"make -j"
~~~~~~~~~

The first of all workflow engines is called 'make'. It builds a tree of interdepending jobs and executes them in order. The '-j' option allows the user to specify a number of jobs to be run simultaneously to speed up execution. The syntax of make is notoriously terse, partly due to it's long heritage (from 1976). This example shows how we can write a script that compiles a C/C++ program using GCC using Python, then how we can parallelise it using Noodles.



