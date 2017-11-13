
term_codes = {
    'fg':        (38, ';2;{0};{1};{2}'.format, 'm'),
    'bg':        (48, ';2;{0};{1};{2}'.format, 'm'),
    'bold':      (1,  'm'),
    'underline': (4,  'm'),
    'regular':   (23, 'm'),
    'italic':    (3,  'm'),
    'reset':     (0,  'm'),
    'back':      (lambda n=1: str(n), 'D'),
    'forward':   (lambda n=1: str(n), 'C'),
    'newline':   ('1E',),
    'up':        ('{0}'.format, 'A'),
    'down':      ('{0}'.format, 'B'),
    'save':      ('s',),
    'restore':   ('u',),
    'move':      ('{0};{1}'.format, 'H'),
    'clear':     ('2J',),
    'reverse':   ('7m',)}


def make_escape(cmd, *args):
    def f(x):
        if hasattr(x, '__call__'):
            return x(*args)
        else:
            return str(x)

    return '\033[' + ''.join(map(f, term_codes[cmd]))


class OutStream:
    def __init__(self, f):
        self.f = f

    def __lshift__(self, x):
        """Emulate the much liked C++ syntax for chaining output."""
        if isinstance(x, list):
            self.f.write(make_escape(*x))
            self.f.flush()
            return self

        if isinstance(x, str):
            self.f.write(x)
            self.f.flush()
            return self

        raise TypeError
