#!/usr/bin/env python
# Test setup to minimize the number of imports from atocha.

g = globals().copy()
from atocha import *
g2 = globals().copy()

gg = set(g2) - set(g)
gg.remove('g')
for key in gg:
    print key

