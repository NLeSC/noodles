
class JobException(Exception):
    def __init__(self, exc_type, exc_value, exc_tb):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.exc_tb = exc_tb

    def reraise(self):
        raise self.exc_value.with_traceback(self.exc_tb)

    def __iter__(self):
        return iter((self.exc_type, self.exc_value, self.exc_tb))
