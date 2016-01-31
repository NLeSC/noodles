Noodles build system: BOIL
==========================

This example shows how to enhance your daily workflow with Noodles! The program
reads a file `boil.ini` from the current directory and starts to compile your
favourite C/C++ project. Dependencies for each source file are being checked
using `gcc -MM` and files are only compiled when the dependcies are newer.
The user can give the `-j` parameter to determine how many jobs should run
simultaneously.

If you look at the BOIL source code, you may notice that very little of the
parallelism of this code creeps into the basic logic of the program.


Testing BOIL
~~~~~~~~~~~~

To test BOIL we provided a small C++ program. There is a main program and
a unittest which can be compiled separately using the given configuration
in `boil.ini`.