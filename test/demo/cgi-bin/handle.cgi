#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for handle.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()
import setup_cgi

from demo import *
r = handler_handle(cgi.FieldStorage(), 'query.cgi')
print 'Content-type: text/html\n\n'
print r
