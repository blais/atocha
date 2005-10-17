#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for handle.
"""

# stdlib imports
import cgi, cgitb; cgitb.enable()
from common import handler_handle

handler_handle(cgi.FieldStorage())
