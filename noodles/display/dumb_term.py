from .pretty_term import OutStream
import sys


class DumbDisplay:
    """Monochrome, dumb term display"""
    def __init__(self, error_filter=None):
        self.jobs = {}
        self.out = OutStream(sys.stdout)
        self.errors = []
        self.error_filter = error_filter

    def start(self, key, job, _):
        if job.hints and 'display' in job.hints:
            self.add_job(key, job.hints)
            self.out << job.hints['display'].format(
                **job.bound_args.arguments) << "\n"

    def done(self, key, data, msg):
        pass

    def error(self, key, _, msg):
        pass

    def add_job(self, key, hints):
        for k in self.jobs:
            self.jobs[k]['line'] += 1
        self.jobs[key] = {'line': 1}
        self.jobs[key].update(hints)

    def error_handler(self, job, xcptn):
        self.errors.append((job, xcptn))

    def report(self):
        if len(self.errors) == 0:
            self.out << "+---(success)\n"

        else:
            self.out << "+---(ERROR!)\n\n"

            for job, e in self.errors:
                msg = 'ERROR '
                if 'display' in job.hints:
                    msg += job.hints['display'].format(
                        **job.bound_args.arguments)
                else:
                    msg += 'calling {} with {}'.format(
                        job.foo.__name__, dict(job.bound_args.arguments)
                    )

                print(msg)
                err_msg = self.error_filter(e)
                if err_msg:
                    print(err_msg)
                else:
                    print(e)

    def __call__(self, key, status, data, err):
        # self.q = q
        # for status, key, data in q.source():
        getattr(self, status)(key, data, err)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self.wait()

        if exc_type:
            if exc_type is KeyboardInterrupt:
                self.out << "\n" << "User interrupt detected, abnormal exit.\n"
                return True

            print("Internal error encountered. Contact the developers.")
            return False

        self.report()

    def wait(self):
        self.q.wait()
