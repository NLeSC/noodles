from .haploid import (pull_map)
from .scheduler import (Result)


@pull_map
def worker(key, job):
    return run_job(key, job)


def run_job(key, job):
    """A worker coroutine. Pulls jobs, yielding results. If an
    exception is raised running the job, it returns a result
    object with 'error' status. If the job requests return-value
    annotation, a two-tuple is expected; this tuple is then
    unpacked, the first being the result, the second part is
    sent on in the error message slot."""
    try:
        if job.hints and 'annotated' in job.hints:
            result, meta_data = job.foo(
                *job.bound_args.args,
                **job.bound_args.kwargs)
            return Result(key, 'done', result, meta_data)

        else:
            result = job.foo(*job.bound_args.args, **job.bound_args.kwargs)
            return Result(key, 'done', result, None)

    except Exception as error:
        return Result(key, 'error', None, error)
