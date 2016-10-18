
class JobException:
    def __init__(self, exc_type, exc_value, exc_tb):
        self.exc_type = exc_type
        self.exc_value = exc_value
        # self.exc_tb = exc_tb

    def reraise(self):
        raise self.exc_value

    def __iter__(self):
        return iter((self.exc_type, self.exc_value, None))

    # def __getstate__(self):
    #     return self.__dict__
    #
    # def __setstate__(self, state):
    #     self.__dict__.update(state)
