#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for query.
"""

# stdlib imports
import cgi, cgitb; cgitb.enable()
from common import handler_query

handler_query(cgi.FieldStorage())
