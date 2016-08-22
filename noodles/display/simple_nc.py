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
    def __init__(self, error_filter=None, title='running jobs'):
        self.jobs = {}
        self.out = OutStream(sys.stdout)
        self.errors = []
        self.error_filter = error_filter or (lambda e: None)
        self.messages = []

        ascii_chars = {
            'check':        'V',
            'fail':         'X',
            'line-hor':     '-',
            'line-ver':     '|',
            'line-tl':      '+',
            'line-bl':      '+'
        }

        utf8_chars = {
            'check':        '✔',
            'fail':         '✘',
            'line-hor':     '─',
            'line-ver':     '│',
            'line-tl':      '╭',
            'line-bl':      '╰'
        }

        self.chars = utf8_chars \
            if sys.stdout.encoding == 'UTF-8' \
            else ascii_chars

        self.out << self.chars['line-tl'] << self.chars['line-hor'] \
                 << '(' << title << ')' << "\n"

    def start(self, key, job, _):
        if job.hints and 'display' in job.hints:
            if key not in self.jobs:
                msg = job.hints['display'].format(
                    **job.bound_args.arguments)[:70]
                self.add_job(key, job, msg)
                self.out << self.chars['line-ver'] << "    " << msg << "\n"
            else:
                self.out << ['save'] << ['up', self.jobs[key]['line']] \
                    << ['forward', max(50, self.jobs[key]['length'] + 2)]
                self.out << "( )" << ['restore']

    def done(self, key, data, msg):
        if key in self.jobs and 'confirm' in self.jobs[key]:
            self.out << ['save'] << ['up', self.jobs[key]['line']] \
                << ['forward', max(50, self.jobs[key]['length'] + 2)]
            self.out << "(" << ['fg', 60, 180, 100] << self.chars['check'] \
                << ['reset'] << ")" << ['restore']

        if key in self.jobs and msg:
            self.message_handler(self.jobs[key], msg)

    def schedule(self, key, job, _):
        if job.hints and 'display' in job.hints:
            msg = job.hints['display'].format(**job.bound_args.arguments)[:70]
            self.add_job(key, job, msg)
            self.out << self.chars['line-ver'] << " " << msg << "\n"

    def retrieved(self, key, data, msg):
        if key in self.jobs and 'confirm' in self.jobs[key]:
            self.out << ['save'] << ['up', self.jobs[key]['line']] \
                << ['forward', max(50, self.jobs[key]['length'] + 2)]
            self.out << "(" << ['fg', 60, 180, 100] << "retrieved" \
                << ['reset'] << ")" << ['restore']

        if key in self.jobs and msg:
            self.message_handler(self.jobs[key], msg)

    def error(self, key, _, data):
        if key in self.jobs and 'confirm' in self.jobs[key]:
            self.out << ['save'] << ['up', self.jobs[key]['line']] \
                << ['forward', max(50, self.jobs[key]['length'] + 2)]
            self.out << "(" << ['fg', 240, 100, 60] << self.chars['fail'] \
                << ['reset'] << ")" << ['restore']

    def add_job(self, key, job, msg):
        for k in self.jobs:
            self.jobs[k]['line'] += 1
        self.jobs[key] = {'line': 1, 'job': job, 'length': len(msg)}
        self.jobs[key].update(job.hints)

    def error_handler(self, job, *exception):
        msg = self.error_filter(*exception)
        if msg:
            self.errors.append((job, msg))
            return True
        else:
            return False

    def message_handler(self, job, warning):
        self.messages.append((job['job'], warning))

    def report(self):
        if len(self.errors) == 0:
            self.out << self.chars['line-bl'] << self.chars['line-hor'] \
                     << "(success)\n"

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
            self.out << self.chars['line-bl'] << self.chars['line-hor'] \
                     << "(" << ['fg', 240, 100, 60] << "ERROR!" \
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
                print(e)

    def __call__(self, key, status, data, err_msg):
        getattr(self, status)(key, data, err_msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self.wait()

        if exc_type:
            if exc_type is KeyboardInterrupt:
                self.out << "\n" << ['fg', 255, 200, 50] \
                         << "User interrupt detected, abnormal exit.\n" \
                         << ['reset']
                return True

            if exc_type is SystemExit:
                return False

            print("Internal error encountered. Contact the developers: \n",
                  exc_type, exc_val)
            return False

        self.report()
