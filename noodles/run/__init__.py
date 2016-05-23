"""
The Noodles Runtime
===================

The Noodles runtime can be thought of as a series of components passing each
other messages. At the center of this system is the *scheduler*, which sends
out jobs to a worker and receives results.  This abstracted form of a worker is
implemented as a pair of coroutines.  The job-messages are a two-tuple, having
a key and a job object. The communication of results is done through
four-tuples, as `(key, status, result, message)`. The `key` must be a key
identifying with a previously submitted job. The `status` is one of
'scheduled', 'fizzled', 'started', 'done', 'aborted', 'error'. There can only
be a `result` if the status is `done`, otherwise `result` must be `None`. The
`message` could be an exception object, or any other object, or `None`. How to
treat the contents of a message is up to the *cook* (library implementation).

Handling of errors
~~~~~~~~~~~~~~~~~~

When the returned status is 'aborted', this means that there was some internal
error in the runtime; for example, a node at the cluster killed your job!  If a
thread is guarded against such things happening (an exception is raised) it
should notify the scheduler about all outstanding jobs on that node with an
'aborted' status. The logical thing to do for the scheduler is then to reschedule
these jobs on a different machine.

The 'fizzled' status means that the job could not start in the first place. Maybe
a resource that we need access to is unavailable. The default behaviour is not to
restart fizzled jobs unless a user intervenes.

The user has every option to catch errors himself, and change the program logic
accordingly. For instance, if we do a parameter sweep over a function that doesn't
converge or is undefined for some value, we may want to proceed with the rest of
the computation. It is the responsibility of the user (and the cook) to catch
all exceptions before they reach Noodles. If an exception does get through, the
worker will return a status 'error' and put the exception in the message field.
Then we can do three things: kill everything, wait for outstanding jobs to finish
(graceful exit), or
ignore that there was an error and put `None` for a result. In the last case the
exception should be a `Warning`. For all other situations the default behaviour is
the graceful exit. To stop all work being done the user can give a keyboard interupt.
"""

