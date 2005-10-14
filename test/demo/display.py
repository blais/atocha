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
if 'rtype' in db and db['rtype'] == 'text':
    r = TextDisplayRenderer(form1, values or {}, incomplete=1,
                            show_hidden=1,
                            output_encoding='latin-1')
    contents = r.render()
else:
    from htmlout import tostring
    r = HoutDisplayRenderer(form1, values or {}, incomplete=1,
                            show_hidden=1)
    contents = tostring(r.render(), encoding='latin-1')

s = StringIO.StringIO()
print >> s, '<div id="buttons">'
print >> s, '<a href="query.cgi" id="edit" class="button">EDIT VALUES</a>'
print >> s, '<a href="reset.cgi" id="edit" class="button">RESET</a>'
print >> s, '</div>'

print >> s, '</div>'
print >> s, '<div>'
print >> s, '<h2>Repr of Parsed Accepted Values</h2>'
print >> s, '<pre id="values-repr">'
for name, value in values.iteritems():
    print >> s, '%s: %s' % (name, repr(value))
print >> s, '</pre>'
contents += s.getvalue()

# Set form data for edit.
sys.stdout.write(template_pre % {'title': 'Form Display',
                                 'uimsg': '',
                                 'scripts': ''})
sys.stdout.write(contents)
sys.stdout.write(template_post)
