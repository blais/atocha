#!/usr/bin/env python
#
# $Id$
#

"""
Handler for form submission.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()
from pprint import pformat

# atocha imports.
from common import *
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
values = p.getvalues(1)

# Handle file upload.
if p['photo']:
    # Read in photograph file, if there is one.
    db['photo-%s' % form1.name] = p['photo'].read()
    db['photofn-%s' % form1.name] = p['photo'].filename
else:
    db['photo-%s' % form1.name] = db['photofn-%s' % form1.name] = None

db['data-%s' % form1.name] = values


# On success, redirect to render page.  You could decide to display results
# from here.
print 'Location: %s' % 'display.cgi'
print
print '302 Success.'
sys.exit(0)

