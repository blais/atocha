#!/usr/bin/env python
#
# $Id$
#

"""
Setup for CGI scripts, and Atocha configuration.
This needs be done only once for a web application.
"""

# stdlib imports.
import sys
from os.path import *
projects_root = dirname(dirname(dirname(dirname(dirname(sys.argv[0])))))
import os

# atocha imports.
sys.path.append(join(projects_root, 'atocha', 'lib', 'python'))
from atocha import *
from atocha.norms.ncgi import CGINormalizer

# htmlout imports (if available).
sys.path.append(join(projects_root, 'htmlout', 'lib', 'python'))
try:
    import htmlout
    from htmlout import *
    from atocha.renderers.rhtmlout import *
except ImportError:
    pass # We won't be able to test the htmlout renderers.

# atocha demo imports.
sys.path.append(join(projects_root, 'atocha', 'test', 'demo'))
import demo


demo.ext = '.cgi'


#-------------------------------------------------------------------------------
#
def do_redirect( url, form, status, message, values, errors ):
    # Store form data for later retrieval in session data.
    db = demo.getdb()
    db['session-%s' % demo.form1.name] = values, errors, message

    print 'Location: %s' % url
    print
    print '302 Errors in user input.'
    sys.exit(0)

# Setup automatic redirection mechanism.
FormParser.redirect_func = staticmethod(do_redirect)

# Setup normalizer for CGI scripts using Python's cgi module.
FormParser.normalizer = CGINormalizer()

# Setup form renderer for rendering scripts.
TextFormRenderer.scriptsdir = 'resources/scripts'
if 'htmlout' in globals():
    HoutFormRenderer.scriptsdir = 'resources/scripts'
