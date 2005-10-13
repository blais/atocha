#!/usr/bin/env python
#
# $Id$
#

"""
Handler for form submission.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()

# atocha imports.
from testcommon import *
from atocha import *


cargs = cgi.FieldStorage()
p = FormParser(form1, cargs, 'query.cgi')

if 'merengue' in (p['dances'] or []):
    repldances = list(p['dances'])
    repldances.remove('merengue')
    p.error(u'Please fix error in dances below. I thought you were cuban.',
            dances=(u'No dominican dances here, please.', repldances))

p.end()

# Set final data in database and remove session data.
db = getdb()
db['data-%s' % form1.name] = p.getvalues()


# On success, redirect to render page.  You could decide to display results
# from here.
print 'Location: %s' % 'display.cgi'
print
print '302 Success.'
sys.exit(0)

