# Note: you will need py.test from pydev.

PYTEST ?= $(HOME)/src/dist-py/py/bin/py.test

PY = python2.3
CMD =  $(PYTEST) -s -x

all: dbg

dbg:
	$(PY) $(CMD) atochatests.py

# opt:
# 	$(PY) -O $(CMD) atochatests.py

