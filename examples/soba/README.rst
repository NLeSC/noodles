==============================================
SOBA: Utility for non-directed graph execution
==============================================

Noodles gives a way to execute directed acyclic graphs. There are use cases where
the graph just gives us mutual exclusion of jobs, because they are writing to the
same output location (either memory or disk). In this case we want to do the
scheduling of jobs dynamically, with the exclusion information added as meta-data.

For this example, we have the graph being fed as a JSON file. We add a worker broker
to the pool to deal with just this problem.
