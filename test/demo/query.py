#!/usr/bin/env python
#
# $Id$
#

"""
CGI handler for rendering a query form to allow the user to enter input.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()

# atocha imports.
from common import *
from atocha import *


# Get old form data to fill the initial values of the form.
db = getdb()
# Fetch the real data.
values, errors, message = db.get('data-%s' % form1.name, {}), None, None

# Fetch the session data.
if 'session-%s' % form1.name in db:
    sessvalues, errors, message = db.get('session-%s' % form1.name,
                                         (None, None, None))
    # Remove that session data (we've used it).
    del db['session-%s' % form1.name]

    # Update session values with newly parsed values.
    if sessvalues:
        values.update(sessvalues)

# Create a form renderert to render the form..
if rtype == 'text':
    r = TextFormRenderer(form1, values, errors,
                         output_encoding='latin-1')
    rendered = r.render(action='handle.cgi')
    scripts = r.render_scripts()
else:
    from htmlout import tostring
    r = HoutFormRenderer(form1, values, errors)
    rendered = tostring(r.render(action='handle.cgi'), encoding='latin-1')
    scripts = [tostring(x, encoding='latin-1') for x in r.render_scripts()]
    scripts = '\n'.join(scripts)

# Render the page (see template in other module).
uimsg = message and '<div id="message">%s</div>' % message or ''
sys.stdout.write(template_pre % {'title': 'Form Render and Handling',
                                 'uimsg': uimsg,
                                 'scripts': scripts})

# Here, we use the form render:
sys.stdout.write(rendered)
sys.stdout.write(template_post)

