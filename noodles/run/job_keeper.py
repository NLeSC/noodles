import uuid


class JobKeeper(dict):
    def __init__(self):
        super(JobKeeper, self).__init__()

    def register(self, job):
        key = uuid.uuid1()
        self[key] = job
        return key, job.node

    def store_result(self, key, status, value, err):
        if status != 'done':
            return

        job = self[key]
        job.node.result = value

