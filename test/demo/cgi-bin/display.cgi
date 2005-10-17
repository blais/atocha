#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for display.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()
sys.path.append('..')
from demo import *

setup_cgi()
handler_display()
