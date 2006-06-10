#!/usr/bin/env python
#
# $Id$
#
#  Atocha -- A web forms rendering and handling Python library.
#  Copyright (C) 2005  Martin Blais
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
Setup for CGI scripts, and Atocha configuration.
This needs be done only once for a web application.
"""

# stdlib imports
import sys
from os.path import *
projects_root = dirname(dirname(dirname(dirname(dirname(sys.argv[0])))))
import os

# atocha imports
sys.path.append(join(projects_root, 'atocha', 'lib', 'python'))
from atocha import *
from atocha.norms.ncgi import normalize_args

# htmlout imports (if available).
sys.path.append(join(projects_root, 'htmlout', 'lib', 'python'))
try:
    import htmlout
    from htmlout import *
    from atocha.renderers.rhtmlout import *
except ImportError:
    pass # We won't be able to test the htmlout renderers.

# atocha demo imports
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
FormParser.normalizer = normalize_args

# Setup form renderer for rendering scripts.
TextFormRenderer.scriptsdir = 'resources/scripts'
if 'htmlout' in globals():
    HoutFormRenderer.scriptsdir = 'resources/scripts'
