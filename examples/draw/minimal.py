from noodles.tutorial import (add, sub, mul)
from noodles.draw_workflow import draw_workflow


u = add(5, 4)
v = sub(u, 3)
w = sub(u, 2)
x = mul(v, w)

draw_workflow("callgraph-a.pdf", x._workflow)
