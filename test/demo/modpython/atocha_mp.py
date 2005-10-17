#!/usr/bin/env python
#
# $Id$
#

"""
mod_python handler for Atocha demo.
"""

# stdlib imports.
import sys
from os.path import dirname, join

# mod_python imports.
from mod_python import apache
from mod_python.util import FieldStorage, Field

    
#-------------------------------------------------------------------------------
#
setup_done = 0

def setup_mp( demo_root ):
    """
    Global setup for Atocha in mod_python.
    """
    # Add paths for include.
    projects_root = dirname(dirname(dirname(dirname(demo_root))))
    sys.path.append(join(projects_root, 'htmlout', 'lib', 'python'))
    sys.path.append(join(projects_root, 'atocha', 'lib', 'python'))
    sys.path.append(join(projects_root, 'atocha', 'test', 'demo'))

    global demo
    import demo

    # Set extensions for our resources.
    demo.ext = ''

    # Define and configure redirection mechanism.
    def do_redirect( url, form, status, message, values, errors ):
        # Store form data for later retrieval in session data.
        db = demo.getdb()
        db['session-%s' % demo.form1.name] = values, errors, message
        raise Redirect('Errors in user input', url)
    
    from atocha import FormParser, TextFormRenderer
    from atocha.norms.nmodpython import ModPythonNormalizer

    # Setup automatic redirection mechanism.
    FormParser.redirect_func = staticmethod(do_redirect)

    # Setup normalizer for CGI scripts using Python's cgi module.
    FormParser.normalizer = ModPythonNormalizer()

    # Setup form renderer for rendering scripts.
    TextFormRenderer.scriptsdir = 'resources/scripts'
    try:
        import htmlout
        from atocha import HoutFormRenderer
        HoutFormRenderer.scriptsdir = 'resources/scripts'
    except ImportError:
        pass


#-------------------------------------------------------------------------------
#
class Redirect(Exception):
    """
    Exception used to trigger redirection.
    """

#-------------------------------------------------------------------------------
#
def handler( mpreq ):
    """
    mod_python handler. We dispatch to the methods in demo.py.
    """
    demo_root = mpreq.get_options()['DemoRoot']
    relpath = mpreq.filename[ len(demo_root): ]
    print >> sys.stderr, '-------------------> %s' % relpath; sys.stderr.flush()
    
    global setup_done
    if not setup_done:
        setup_mp(demo_root)

    rcode = apache.OK
    try:
        mpreq.content_type = 'text/html'
        if relpath == '/display':
            out = demo.handler_display()

        elif relpath == '/query':
            out = demo.handler_query()

        elif relpath == '/handle':
            out = demo.handler_handle(mpreq, '/query')

        elif relpath == '/reset':
            out = demo.handler_reset()

        else:
            out = ''
            rcode = 404

        mpreq.write(out)

    except Redirect, e:
        # Handler redirection exception triggered from handler.
        msg, url = e.args
        mpreq.err_headers_out.add('Location', url)
        rcode = 302
        
    return rcode
