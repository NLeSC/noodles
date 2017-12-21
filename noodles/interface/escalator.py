from .functions import (lift)


class Escalator:
    """An |Escalator| object gets automaticall `lifted` in the deep-copy stage
    of workflow evaluation. If you have an object that inherently contains
    promises, consider deriving it from |Escalator|.

    .. |Escalator| replace:: :py:class:`Escalator`"""
    def __deepcopy__(self, memo):
        return lift(self)
