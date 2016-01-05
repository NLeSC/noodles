import sys


class Log:
    def worker_stderr(self, wid, msg):
        print(
            "worker {0}: {1}".format(wid, msg.strip()),
            file=sys.stderr, flush=True)


log = Log()
