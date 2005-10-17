#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for display.
"""

# stdlib imports
import cgi, cgitb; cgitb.enable()
from common import handler_display

handler_display(cgi.FieldStorage())
