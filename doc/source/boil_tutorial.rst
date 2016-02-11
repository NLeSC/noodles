.. highlight:: python
    :linenothreshold: 5


Real World Tutorial 1: Boil, a make tool.
=========================================

.. toctree::

    boil_source

This tutorial should teach you the basics of using Noodles to parallelise a Python program. We will see some of the quirks that come with programming in a strict functional environment.

"make -j"
~~~~~~~~~

The first of all workflow engines is called 'make'. It builds a tree of interdepending jobs and executes them in order. The '-j' option allows the user to specify a number of jobs to be run simultaneously to speed up execution. The syntax of make is notoriously terse, partly due to it's long heritage (from 1976). This example shows how we can write a script that compiles a C/C++ program using GCC or CLANG, then how we can parallelise it using Noodles. We have even included a small C++ program to play with!

Functions
~~~~~~~~~

Compiling a C program is a two-stage process. First we need to compile each source file to an object file, then link these object files to an executable. The :py:func:`compile_source` function looks like this::

    @schedule
    def compile_source(source_file, object_file, config):
        p = subprocess.run(
            [config['cc'], '-c'] + config['cflags'].split() \
                + [source_file, '-o', object_file],
            stderr=subprocess.PIPE, universal_newlines=True)
        p.check_returncode()

        return object_file

It takes a source file, an object file and a configuration object. This configuration contains all the information on which compiler to use, with which flags, and so on. If the compilation was successful, the name of the object file is returned. This last bit is crucial if we want to include this function in a workflow.

.. NOTE:: Each dependency (in this case linking to an excecutable requires compilation first) should be represented by return values of one function ending up as arguments to another function.

The function for linking object files to an executable looks very similar::

    @schedule
    def link(object_files, config):
        p = subprocess.run(
            [config['cc']] + object_files + ['-o', config['target']] \
                + config['ldflags'].split(),
            stderr=subprocess.PIPE, universal_newlines=True)
        p.check_returncode()

        return config['target']

In this case the function takes a list of object file names and the same configuration object that we saw before. Again, this function returns the name of the target executable file. The caller of this function already knows the name of the target file, but we need it to track dependencies.

Since both the :py:func:`link` and the :py:func:`compile_source` functions do actual work that we'd like to see being done in a concurrent environment, they need to be decorated with the :py:func:`schedule` decorator.

One of the great perks of using Make, is that it skips building any files that are already up-to-date with the source code. If our little build script is to compete with such efficiency, we should do the same!

::

    def is_out_of_date(f, deps):
        if not os.path.exists(f):
            return True

        f_stat = os.stat(f)

        for d in deps:
            d_stat = os.stat(d)

            if d_stat.st_mtime_ns > f_stat.st_mtime_ns:
                return True

        return False

This function takes a file `f` and a list of files `deps` and checks the modification dates of all of the files in `deps` against that of `f`.

One of the *quirks*, that we will need to deal with, is that some *logic* in a program needs to have knowledge of the actual objects that are computed, not just the possibility of such an object in the future. When designing programs for Noodles, you need to be aware that such logic can only be performed *inside* the functions. Say we have a condition under which one or the other action needs to be taken, and this condition depends on the outcome of a previous element in the workflow. The actual Python `if` statement evaluating this condition needs to be inside a scheduled function. One way around this, is to write a wrapper::

    @schedule
    def cond(predicate, when_true, when_false):
        if predicate:
            return when_true
        else:
            return when_false

However, there is a big problem with this approach! The Noodles engine sees two arguments to the `cond` function that it wants to evaluate before heading into the call to `cond`. Both arguments will be evaluated before we can even decide which of the two we should use! We will present a solution to this problem at a later stage, but for now we will have to work our way around this by embedding the conditional logic in a more specific function.


In this case we have the function `is_out_of_date` that determines whether we need to recompile a file or leave it as it is. The second stage, linking the object files to an executable, only needs to happen if any of the object files is younger than the executable. However these object files are part of the logic inside the workflow! The conditional execution of the linker needs to be called by another scheduled function::

    @schedule
    def get_target(obj_files, config):
        if is_out_of_date(config['target'], obj_files):
            return link(obj_files, config)
        else:
            return message("target is up-to-date.")

Since we need the answer to :py:func:`is_out_of_date` in the present, the :py:func:`is_out_of_date` function cannot be a scheduled function. Python doesn't know the truth value of a :py:class:`PromisedObject`. The `message` function is not a special function; it just prints a message and returns a value (optional second argument). We still need to optionalise the compilation step. Since all of the information needed to decide whether to compile or not is already present, we can make this a normal Python function; there is no need to schedule anything (even though everything would still work if we did)::

    def get_object_file(src_dir, src_file, config):
        obj_path = object_filename(src_dir, src_file, config)
        src_path = os.path.join(src_dir, src_file)

        deps = dependencies(src_path, config)
        if is_out_of_date(obj_path, deps):
            return compile_source(src_path, obj_path, config)
        else:
            return obj_path


The `object_filename` is a little helper function creating a sensible name for the object file; also it makes sure that the directory in which the object file is placed exists. `dependencies` Runs the compiler with '-MM' flags to obtain the header dependencies of the C-file.

We are now ready to put these functions together in a workflow!

::

    def make_target(config):
        dirs = [config['srcdir']] + [
            os.path.normpath(os.path.join(config['srcdir'], d))
            for d in config['modules'].split()
        ]

        files = chain(*(
            find_files(d, config['ext'])
            for d in dirs)
        )

        obj_files = noodles.gather(*[
            get_object_file(src_dir, src_file, config)
            for src_dir, src_file in files
            ])

        return get_target(obj_files, config)

Let's go through this step-by-step. The `make_target` function takes one argument, the config object. We obtain from the configuration the directories to search for source files. We then search these directories for any files with the correct file extension, stored in `config['ext']`. The variable `files` now contains a list of pairs, each pair having a directory and file name. So far we have not yet used any Noodles code.

Next we pass each source file through the `get_object_file` function in a list comprehension. The resulting list contains both :py:class:`PromisedObject` and string values; strings for all the object files that are already up-to-date. To pass this list to the linking stage we have to make sure that Noodles understands that the list is something that is being promised. If we were to pass it as is, Noodles just sees a list as an argument to `get_target` and doesn't look any deeper.

.. NOTE:: Every `PromisedObject` has to be passed as an argument to a scheduled function in order to be evaluated. To pass a list to a scheduled function, we have to convert the list of promises into a promise of a list.

The function :py:func:`gather` solves this little problem; it's definition is very simple::

    @schedule
    def gather(*args):
        return list(args)

Now that the variable `obj_files` is a :py:class:`PromisedObject`, we can pass it to `get_target`, giving us the final workflow. Running this workflow can be as simple as ``run_single(wf)`` or ``run_parallel(wf, n_threads=4)``.

Friendly output and error handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The code as defined above will run, but if the compiler gives error messages it will crash in a very ugly manner. Noodles has some features that will make our fledgeling Make utility much prettier. We can decorate our functions further with information on how to notify the user of things happening::

    @schedule_hint(display="Compiling {source_file} ... ",
                   confirm=True)
    def compile_source(source_file, object_file, config):
        pass

The :py:func:`schedule_hint` decorator attaches hints to the scheduled function. These hints can be used in any fashion we like, depending on the workers that we use to evaluate the workflow. In this case we use the :py:func:`run_logging` worker, with the :py:class:`SimpleDisplay` class to take care of screen output::

    with SimpleDisplay(error_filter) as display:
        noodles.run_logging(work, args.n_threads, display)

The `error_filter` function determines what errors are expected and how we print the exceptions that are caught. In our case we expect exceptions of type :py:exc:`subprocess.CalledProcessError` in the case of a compiler error. Otherwise the exception is unexpected and should be treated as a bug in Boil!

::

    def error_filter(xcptn):
        if isinstance(xcptn, subprocess.CalledProcessError):
            return xcptn.stderr
        else:
            return None

The `display` tag in the hinst tells the `display` object to print a text when the job is started.
The `confirm` flag in the hints tells the `display` object that a function is error-prone and to draw a green checkmark on success and a red X in case of failure.

Conclusion
~~~~~~~~~~

You should now be able to fully understand the sourcecode of Boil! Try it out on the sample code provided:

.. code-block:: bash

    > ./boil --help
    
.. code-block:: none

    usage: boil [-h] [-j N_THREADS] [-dumb] target

    Compile software. Configuration is in 'boil.ini'.

    positional arguments:
      target        target to build, give 'list' to list targets.

    optional arguments:
      -h, --help    show this help message and exit
      -j N_THREADS  number of threads to run simultaneously.
      -dumb         print info without special term codes.

.. code-block:: bash

    > cat boil.ini

.. code-block:: ini

    [generic]
    objdir = obj
    ldflags = -lm
    cflags = -g -std=c++11 -O2 -fdiagnostics-color -Wpedantic
    cc = g++
    ext = .cc

    [main]
    srcdir = main
    target = hello
    modules = ../src

    [test]
    srcdir = test
    target = unittests
    modules = ../src

    [clean]
    command = rm -rf ${generic:objdir} ${test:target} ${main:target}


.. code-block:: bash
    
    > ./boil main -j4

.. code-block:: none

    ╭─(Building target hello)
    │   Compiling src/mandel.cc ...                   (✔)
    │   Compiling src/common.cc ...                   (✔)
    │   Compiling src/render.cc ...                   (✔)
    │   Compiling src/iterate.cc ...                  (✔)
    │   Compiling src/julia.cc ...                    (✔)
    │   Compiling main/main.cc ...                    (✔)
    │   Linking ...                                   (✔)
    ╰─(success)

