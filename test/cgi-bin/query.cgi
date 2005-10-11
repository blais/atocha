#!/usr/bin/env python
#
# $Id$
#

"""
Test renderer for fields.
"""

# stdlib imports
import sys, os, shelve
from os.path import *
import cgi, cgitb; cgitb.enable()
from pprint import pprint, pformat

# atocha imports.
root = dirname(dirname(dirname(sys.argv[0])))
sys.path.append(join(root, 'lib', 'python'))
from atocha import *

# atocha test imports.
from testcommon import *


#-------------------------------------------------------------------------------
#
def main():
    """
    CGI handler for rendering a form to the user.
    """

    # Get form data.
    sdata = SessionData()
    values, errors, message = sdata.getformdata(form1.name)
    sdata.setformdata(form1.name, None, None)

    r = TextFormRenderer(form1, values, errors,
                         output_encoding='latin-1')

    uimsg = message and '<div id="message">%s</div>' % message or ''
    sys.stdout.write(template_pre % {'title': 'Test Form Query/Render',
                                     'uimsg': uimsg,
                                     'scripts': r.render_scripts()})
    
    sys.stdout.write(r.render(action='handle.cgi'))
    sys.stdout.write(template_post)

if __name__ == '__main__':
    main()

