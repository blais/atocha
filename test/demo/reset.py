#!/usr/bin/env python
#
# $Id$
#

"""
Handler that resets the form data stored in the local DB.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()

# atocha imports.
from testcommon import *


# Set form data for edit.
db = getdb()
for n in 'data', 'session':
    try:
        del db['%s-%s' % (n, form1.name)]
    except Exception:
        pass

# Redirect to query page. 
print 'Location: %s' % 'display.cgi'
print
print '302 Values reset.'
sys.exit(0)
