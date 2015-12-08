from inspect import isfunction

term_codes = {
    'fg':        (38, lambda r, g, b: ";2;{0};{1};{2}".format(r, g, b), 'm'),
    'bg':        (48, lambda r, g, b: ";2;{0};{1};{2}".format(r, g, b), 'm'),
    'bold':      (1,  'm'),
    'underline': (4,  'm'),
    'regular':   (22, 'm'),
    'italic':    (3,  'm'),
    'reset':     (0,  'm'),
    'back':      (lambda n=1: str(n), 'D'),
    'forward':   (lambda n=1: str(n), 'C'),
    'newline':   ('1E',)}


def make_escape(cmd, *args):
    def f(x):
        if isfunction(x):
            return x(*args)
        else:
            return str(x)

    return "\033[" + ''.join(map(f, term_codes[cmd]))


class OutStream:
    def __init__(self, f):
        self.f = f

    def __lshift__(self, x):
        if isinstance(x, list):
            self.f.write(make_escape(*x))
            self.f.flush()
            return self

        if isinstance(x, str):
            self.f.write(x)
            self.f.flush()
            return self

        raise TypeError
