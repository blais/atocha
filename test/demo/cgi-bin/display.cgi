#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for display.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()
import setup_cgi

from demo import *
r = handler_display()
print 'Content-type: text/html\n\n'
print r

