import sys
import os
import curses
import termios


class termcap(dict):
    """This is a dictionary class that stores all required termios capabilities
    for you. Just initialize it with a dictionary containing three list of
    strings. A list for boolean (or flag caps) called 'flag', a 'num' list for
    numerical caps, and a 'str' for strings. Or just leave it empty, and add
    the items manually later on."""
    def __init__(self, cap_list):
        dict.__init__(self)

        for i in cap_list['flag']:
            self.getflag(i)

        for i in cap_list['num']:
            self.getnum(i)

        for i in cap_list['str']:
            self.getstr(i)

    def getstr(self, capname):
        self[capname] = curses.tigetstr(capname)
        if self[capname] is None:
            raise RuntimeError(
                'This terminal is not capable of doing ' + capname)

    def getnum(self, capname):
        self[capname] = curses.tigetnum(capname)
        if self[capname] is None:
            raise RuntimeError(
                'This terminal is not capable of doing ' + capname)

    def getflag(self, capname):
        self[capname] = curses.tigetflag(capname)
        if self[capname] is None:
            raise RuntimeError(
                'This terminal is not capable of doing ' + capname)


class ostream:
    def __init__(self, fo, caps, extra=None):
        self.fo = fo
        self.caps = caps
        self.extra = extra

    def __lshift__(self, q):
        if isinstance(q, str):
            self.fo.write(q)

        elif isinstance(q, list):
            cmd = q[0]
            args = q[1:]

            if cmd in self.caps:
                self.fo.write(curses.tparm(
                    self.caps[cmd], *args).decode('ascii'))
            elif self.extra and cmd in self.extra:
                self.fo.write(self.extra[cmd](*args))
            else:
                raise RuntimeError('Could not find terminfo code: ' + cmd)

        elif hasattr(q, '__iter__'):
            for item in q:
                self << item

        self.fo.flush()
        return self


class TermApp(ostream):
    required_caps = {
        'flag': [
            # mainly for my debugging pursoses, as the currents set of caps
            # should work for all xterm and rxvt derivates
            'bce', 'ccc', 'cpix', 'crxm', 'km', 'hs', 'lpix', 'da',
            'db', 'mir', 'ndscr', 'nrrmc', 'sam', 'eslok', 'xon',
        ],
        'num': [
            'cols',        # number of columns
            'lines',    # number of lines
            'colors',    # number of colors, preferably 8.
        ],
        'str': [
            'cup',        # move cursor to #1, #2
            'cud',        # cursor down
            'cuu',        # cursor up
            'cub',        # cursor back
            'cuf',        # cursor forward
            'cr',        # cariage return
            'sc',        # save cursor
            'rc',        # restore cursor

            'civis',    # invisible cursor
            'cnorm',    # visible cursor

            'clear',    # clear the entire screen
            'el1',        # clear to beginning of line
            'el',        # clear to end of line
            'ed',        # clear to end of display
            'dch',        # clear n chars
            'dl',        # delete n lines

            'op',        # reset terminal colors
            'sgr0',        # turn off attributes
            'sitm',     # italics
            'bold',        # bold mode
            'rev',        # reverse mode
            'smul',        # underline mode
            'setab',    # set background
            'setaf'    # set foreground
            # 'setb',    # set background
            # 'setf',    # set foreground
        ]
    }

    def __init__(self):
        self.input = sys.stdin
        self.output = sys.stdout

        curses.setupterm(os.getenv("TERM"), self.output.fileno())
        caps = termcap(self.required_caps)
        extra = {
            'setfg': '\033[38;2;{0};{1};{2}m'.format,
            'setbg': '\033[48;2;{0};{1};{2}m'.format
        }

        super(TermApp, self).__init__(self.output, caps, extra)

    def __enter__(self):
        curses.setupterm()
        self.orig_attr = termios.tcgetattr(self.output.fileno())

        self.new_attr = list(self.orig_attr)  # make a copy
        self.new_attr[3] &= ~(termios.ECHO | termios.ICANON)
        self.new_attr[6][termios.VMIN] = 0
        self.new_attr[6][termios.VTIME] = 0
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore_term()

    def restore_term(self):
        self << "\033[?25h"  # cursor on
        termios.tcsetattr(self.output.fileno(), termios.TCSANOW,
                          self.orig_attr)

    def setup_term(self):
        self << "\033[?25l"  # cursor off
        termios.tcsetattr(self.output.fileno(), termios.TCSANOW,
                          self.new_attr)

    def set_im(self, vt, vm):
        self.new_termios[6][termios.VTIME] = vt
        self.new_termios[6][termios.VMIN] = vm
        termios.tcsetattr(self.output, termios.TCSANOW, self.new_termios)

    def refresh_size(self):
        self.getnum('lines')
        self.getnum('cols')

    def get_cols(self):
        return self.caps['cols']

    def get_lines(self):
        return self.caps['lines']

    def clear(self):
        return self.caps['clear']

    def set_fg(self, c):
        return curses.tparm(self.caps['setaf'], c)

    def set_bg(self, c):
        return curses.tparm(self.caps['setab'], c)

    def set_bold(self):
        return self.caps['bold']

    def set_rv(self):
        return self.caps['rev']

    def set_ul(self):
        return self.caps['smul']

    def moveyx(self, y, x):
        return curses.tparm(self.caps['cup'], y, x)

    def movexy(self, x, y):
        return self.moveyx(y, x)

    def move_down(self, n=1):
        return curses.tparm(self.caps['cud'], n)

    def move_up(self, n=1):
        return curses.tparm(self.caps['cuu'], n)

    def move_left(self, n=1):
        return curses.tparm(self.caps['cub'], n)

    def move_right(self, n=1):
        return curses.tparm(self.caps['cuf'], n)

    def cr(self):
        return self.caps['cr']

    def save_pos(self):
        return self.caps['sc']

    def restore_pos(self):
        return self.caps['rc']

    def cursor_on(self):
        return self.caps['cnorm']

    def cursor_off(self):
        return self.caps['civis']

    def reset_color(self):
        return self.caps['op'] + self.caps['sgr0']
