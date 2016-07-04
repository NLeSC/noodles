from .pretty_term import OutStream
import sys


class Display:
    """A modest display to track jobs being run. The message being printed
    for each job depends on the hints present. This display supports two
    keywords: 'display' and 'check'.

    'display' Gives a string that will be formatted with the arguments to
    the function call.

    'check' Makes sure that the user gets feedback on the success or failure
    of the job, meaning a green V or red X will appear behind the ."""
    def __init__(self, error_filter):
        self.jobs = {}
        self.out = OutStream(sys.stdout)
        self.errors = []
        self.error_filter = error_filter
        self.messages = []

    def start(self, key, job, _):
        if job.hints and 'display' in job.hints:
            msg = job.hints['display'].format(**job.bound_args.arguments)[:70]
            self.add_job(key, job, msg)
            self.out << msg << "\n"

    def done(self, key, data, msg):
        if key in self.jobs and 'confirm' in self.jobs[key]:
            self.out << ['save'] << ['up', self.jobs[key]['line']] \
                << ['forward', max(50, self.jobs[key]['length'] + 2)]
            self.out << "(" << ['fg', 60, 180, 100] << "✔" << ['reset'] \
                << ")" << ['restore']

        if key in self.jobs and msg:
            self.message_handler(self.jobs[key], msg)

    def error(self, key, _, data):
        if key in self.jobs and 'confirm' in self.jobs[key]:
            self.out << ['save'] << ['up', self.jobs[key]['line']] \
                << ['forward', max(50, self.jobs[key]['length'] + 2)]
            self.out << "(" << ['fg', 240, 100, 60] << "✘" << ['reset'] \
                << ")" << ['restore']

    def add_job(self, key, job, msg):
        for k in self.jobs:
            self.jobs[k]['line'] += 1
        self.jobs[key] = {'line': 1, 'job': job, 'length': len(msg)}
        self.jobs[key].update(job.hints)

    def error_handler(self, job, xcptn):
        self.errors.append((job, xcptn))

    def message_handler(self, job, warning):
        self.messages.append((job['job'], warning))

    def report(self):
        if len(self.errors) == 0:
            self.out << "╰─(success)\n"

            if len(self.messages) != 0:
                self.out << "There were warnings: \n\n"

                for job, w in self.messages:
                    msg = 'WARNING '
                    if job.hints and 'display' in job.hints:
                        msg += job.hints['display'].format(
                            **job.bound_args.arguments)
                    else:
                        msg += 'calling {} with {}'.format(
                            job.foo.__name__, dict(job.bound_args.arguments)
                        )
                    print(msg)
                    print(w)

        else:
            self.out << "╰─(" << ['fg', 240, 100, 60] << "ERROR!" \
                     << ['reset'] << ")\n\n"

            for job, e in self.errors:
                msg = 'ERROR '
                if job.hints and 'display' in job.hints:
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

    def __call__(self, q):
        self.q = q
        for status, key, data, err_msg in q.source():
            getattr(self, status)(key, data, err_msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wait()

        if exc_type:
            if exc_type is KeyboardInterrupt:
                self.out << "\n" << ['fg', 255, 200, 50] \
                         << "User interrupt detected, abnormal exit.\n" \
                         << ['reset']
                return True

            print("Internal error encountered. Contact the developers.")
            return False

        self.report()

    def wait(self):
        self.q.wait()
