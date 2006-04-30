#!/usr/bin/env python

"""
List the symbols that are imported after a 'from foo import *'.
"""

import sys as __priv_sys
__priv_orig = set(globals().keys())

from atocha import *

__priv_new = set(globals().keys())

from pprint import pprint
for i in sorted(__priv_new - __priv_orig):
    if i.startswith('__priv_'):
        continue
    print i

