from noodles import (schedule, run_single)
from noodles.tutorial import (add)
from draw_workflow import draw_workflow

@schedule
class A:
    def __init__(self, value):
        self.value = value

    @property
    def square(self):
        return self.value**2

    @square.setter
    def square(self, sqr):
        self.value = sqr**(1/2)


u = A(3)
v = A(4)
u.square = add(u.square, v.square)

draw_workflow("pythagoras.pdf", u.value._workflow)

print("⎷(3² + 4²) = ", run_single(u.value))

