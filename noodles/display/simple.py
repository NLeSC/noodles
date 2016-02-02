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
    def __init__(self):
        self.jobs = {}
        self.out = OutStream(sys.stdout)

    def start(self, key, job):
        if job.hints and 'display' in job.hints:
            self.add_job(key, job.hints)
            self.out << job.hints['display'].format(
                **job.bound_args.arguments) << "\n"

    def done(self, key, data):
        if key in self.jobs and 'confirm' in self.jobs[key]:
            self.out << ['save'] << ['up', self.jobs[key]['line']] \
            << ['forward', 50]
            self.out << "(" << ['fg', 60, 180, 100] << "✔" << ['reset'] \
            << ")" << ['restore']

    def error(self, key, data):
        if key in self.jobs and 'confirm' in self.jobs[key]:
            self.out << ['save'] << ['up', self.jobs[key]['line']] \
            << ['forward', 50]
            self.out << "(" << ['fg', 240, 100, 60] << "✘" << ['reset'] \
            << ")" << ['restore']

    def add_job(self, key, hints):
        for k in self.jobs:
            self.jobs[k]['line'] += 1
        self.jobs[key] = {'line': 1}
        self.jobs[key].update(hints)

    def __call__(self, q):
        self.q = q
        for status, key, data in q.source():
            getattr(self, status)(key, data)

    def wait(self):
        self.q.wait()


