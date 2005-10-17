#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for handle.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()
sys.path.append('..')
from demo import handler_handle

handler_handle(cgi.FieldStorage(), 'query.cgi')
