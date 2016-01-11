from .storable import Storable


class Lambda(Storable):
    """Serializable storage for a lambda-expression.

    The user may want to sprinkle her/his code with little lambda-functions.
    Python lambda functions are not easily storable. One may be tempted to
    use pickle to store the function object, but pickle doesn't load the
    namespace needed to run the function. For instance if the lambda-function
    contains a reference to `math.sin`, `scipy.special.erf` or
    what-have-you-not, pickling will fail to reproduce a working function
    object.

    This class takes a Python expression as a string and uses `eval()`
    to create a working function object. Dependencies can be given in the
    `globals` dict. Those will be saved and imported back when the object is
    loaded."""
    def __init__(self, expression, globals=None, locals=None):
        super(Lambda, self).__init__()

        self.expression = expression
        self.globals = globals
        self.locals = locals
        self.obj = eval(expression, globals, locals)

    def as_dict(self):
        return {'expression': self.expression,
                'globals': self.globals,
                'locals': self.locals}

    @classmethod
    def from_dict(cls, **kwargs):
        return Lambda(**kwargs)

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)
