"""
|▛▀▜|▙▄▟|▗▄▖|▝▀▘|
⌮⌬
○◉□▣◔◑◕●♾⚝☺☹✨✩❄❅❆✾⚛✗✓✔✘
"""

# import sys

from .termapp import TermApp


class Turtle:
    dx = [1, 0, -1, 0]
    dy = [0, -1, 0, 1]

    def __init__(self, x, y, d):
        self.jump(x, y, d)
        self.stack = []

    def turn(self, r):
        self.d = (self.d + r) % 4

    def move(self):
        self.x += Turtle.dx[self.d]
        self.y += Turtle.dy[self.d]

    def push(self):
        self.stack.append((self.x, self.y, self.d))

    def pop(self):
        self.x, self.y, self.d = self.stack[-1]
        del self.stack[-1]

    def jump(self, x, y, d):
        self.x = x
        self.y = y
        self.d = d


class Canvas:
    def __init__(self, width, height, turtle=None):
        self.width = width
        self.height = height
        self.turtle = Turtle(0, 0, 0) if turtle is None else Turtle(*turtle)
        self.field = [[0 for i in range(width)] for j in range(height)]

    def put(self, s):
        for c in s:
            if c == '+':
                self.turtle.turn(1)
                continue

            if c == '-':
                self.turtle.turn(-1)
                continue

            if c == '[':
                self.turtle.push()
                continue

            if c == ']':
                self.turtle.pop()
                continue

            if c.isupper():
                w, h = self.width, self.height
                self.field[self.turtle.y % h][self.turtle.x % w] \
                    |= (1 << self.turtle.d)
                self.turtle.move()
                self.field[self.turtle.y % h][self.turtle.x % w] \
                    |= (1 << ((self.turtle.d+2) % 4))
                continue

            if c.islower():
                self.turtle.move()

        return self

    def render(self):
        chars = " ─│╰──╯┴│╭│├╮┬┤┼"
        return list(map(lambda l: ''.join(
            map(lambda c: chars[c], l)), self.field))


class LSystem:
    def __init__(self, axiom, rules):
        self.axiom = axiom
        self.rules = rules

    def compute(self, n):
        state = self.axiom
        for i in range(n):
            state = ''.join(map(
                lambda c: self.rules.get(c, c),
                state))
        return state


def make_frame(w, h):
    line = 'F' * (w - 1) + '-' + 'F' * (h - 1) \
        + '-' + 'F' * (w - 1) + '-' + 'F' * (h - 1)
    cx = Canvas(w, h)
    cx.put(line)
    return cx.render()


if __name__ == "__main__":
    with TermApp() as tout:
        width = tout.get_cols()
        height = tout.get_lines()

        cx = Canvas(28, 24)
        cx.turtle.jump(13, 17, 0)
        cx.put(LSystem('F', {'F': 'FF-F-'}).compute(6))
        ls = cx.render()

        fr1 = make_frame(width - 18, 7)
        fr2 = make_frame(width - 18, 12)

        tout << tout.reset_color() << ['setfg', 140, 0, 40]
        tout << ['clear'] << ['cup', 1, 1]
        for l in ls:
            tout << ['sc'] << l << ['rc'] << ['cud', 1]
        tout << ['setfg', 170, 110, 10] << ['cup', 10, 10] << 'λみ'

        tout << ['setfg', 50, 120, 90] << ['cup', 5, 16]
        for l in fr1:
            tout << ['sc'] << l << ['rc'] << ['cud', 1]

        tout << ['setfg', 50, 80, 120] << ['cud', 1]
        for l in fr2:
            tout << ['sc'] << l << ['rc'] << ['cud', 1]

        tout << ['setfg', 160, 220, 100] << ['cup', 3, 20]
        tout << ['sitm']
        tout << " Noodles 0.1.0 - worker console "
        tout << ['cup', 4, 20] << ['rev'] << ['setfg', 40, 40, 40] \
             << "▆"*(width - 24)

        tout << ['sgr0'] << ['op'] << ['setfg', 100, 160, 60] << ['sitm']
        tout << ['cup', 5, 19] << "(status)"
        tout << ['cup', 13, 19] << "(job list)"
        tout << ['cup', 25, 1] << ['op'] << ['sgr0']
