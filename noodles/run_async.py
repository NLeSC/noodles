"""
Run a workflow using the `async` and `await` syntax. There is an asynchronous
worker queue represented by an iterator. Each time a job finishes we recieve a
callback, pushing a result. We handle the result, possibly adding new jobs to
the queue. This assumes there is an external queue manager distributing jobs
between workers. This queue manager is also responsible for making the
call-back.

We have several possible queue managers in mind: SLURM, celery, Xenon, and
a local queue manager running jobs in several threads.
"""
