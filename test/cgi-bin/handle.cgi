#!/usr/bin/env python
#
# $Id$
#

"""
Test handler for fields.
"""

# stdlib imports
import sys, os, StringIO
from os.path import *
from pprint import pprint, pformat
import cgi, cgitb; cgitb.enable()

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

    cargs = cgi.FieldStorage()
    p = FormParser(form1, cargs, 'render.cgi')

    if 'merengue' in (p['dances'] or []):
        repldances = list(p['dances'])
        repldances.remove('merengue')
        p.error(u'Please fix error in dances below. I thought you were cuban.',
                dances=(u'No dominican dances here, please.', repldances))

    p.end()
    
    # On success, render as display, with a text rendition at the bottom.
    r = TextDisplayRenderer(form1, p.getvalues(), incomplete=1,
                            output_encoding='latin-1')
    contents = r.render()
    assert isinstance(contents, str) # Sanity check while we're developing.
    
    s = StringIO.StringIO()
    print >> s, '<pre id="values-repr">'
    for name, value in p.getvalues().iteritems():
        print >> s, '%s: %s' % (name, repr(value))
    print >> s, '</pre>'
    print >> s, '<a href="render.cgi">EDIT VALUES</a>'
    contents += s.getvalue()

    # Set form data for edit.
    sdata = SessionData()
    sdata.setformdata(form1.name, p.getvalues())

    sys.stdout.write(template_pre % {'title': 'Successful Form Handling',
                                     'uimsg': ''})
    sys.stdout.write(contents)
    sys.stdout.write(template_post)


if __name__ == '__main__':
    main()

