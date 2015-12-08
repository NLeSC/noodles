# "|▛▀▜|▙▄▟|▗▄▖|▝▀▘|"


class Turtle:
    dx = [1, 0, -1, 0]
    dy = [0, -1, 0, 1]

    def __init__(self, x, y, d):
        self.x = x
        self.y = y
        self.d = d
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

    def render(self, width, height, start, n):
        chars = " ─│╰──╯┴│╭│├╮┬┤┼"
        field = [[0 for i in range(width)] for j in range(height)]
        turtle = start

        for c in self.compute(n):
            if c == '+':
                turtle.turn(1)
                continue

            if c == '-':
                turtle.turn(-1)
                continue

            if c == '[':
                turtle.push()
                continue

            if c == ']':
                turtle.pop()
                continue

            if c.isupper():
                field[turtle.y % height][turtle.x % width] \
                    |= (1 << turtle.d)
                turtle.move()
                field[turtle.y % height][turtle.x % width] \
                    |= (1 << ((turtle.d+2) % 4))
                continue

        return list(map(lambda l: ''.join(
            map(lambda c: chars[c], l)), field))


import sys
from .pretty_term import OutStream

perr = OutStream(sys.stderr)

if __name__ == "__main__":
    ls = LSystem('F', {'F': 'FF-F-'}).render(27, 24, Turtle(12, 17, 0), 6)
    perr << ['fg', 150, 200, 0]
    for l in ls:
        perr << l << '\n'
    perr << ['reset']
