#!/usr/bin/env python
#
# $Id$
#

"""
Render page for final accepted displayed data.
Render with display renderer, with a text rendition at the bottom.
"""

# stdlib imports
import sys, os, StringIO
from os.path import *
import cgi, cgitb; cgitb.enable()

# atocha imports.
from common import *
from atocha import *


# Get data from database.
db = getdb()
values = db.get('data-%s' % form1.name, {})

# Create display renderer to display the data.
r = TextDisplayRenderer(form1, values or {}, incomplete=1,
                        show_hidden=1,
                        output_encoding='latin-1')
contents = r.render()
assert isinstance(contents, str) # Sanity check while we're developing.

s = StringIO.StringIO()
print >> s, '<div id="buttons">'
print >> s, '<a href="query.cgi" id="edit" class="button">EDIT VALUES</a>'
print >> s, '<a href="reset.cgi" id="edit" class="button">RESET</a>'
print >> s, '</div>'
print >> s, '<pre id="values-repr">'
for name, value in values.iteritems():
    print >> s, '%s: %s' % (name, repr(value))
print >> s, '</pre>'
contents += s.getvalue()

# Set form data for edit.
sys.stdout.write(template_pre % {'title': 'Successful Form Handling',
                                 'uimsg': '',
                                 'scripts': ''})
sys.stdout.write(contents)
sys.stdout.write(template_post)
