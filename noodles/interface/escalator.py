from .functions import (lift)


class Escalator:
    def __deepcopy__(self, memo):
        return lift(self)

