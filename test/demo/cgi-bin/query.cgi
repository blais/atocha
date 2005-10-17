#!/usr/bin/env python
#
# $Id$
#

"""
CGI forwarder script for query.
"""

# stdlib imports
import sys, cgi, cgitb; cgitb.enable()
sys.path.append('..')
from demo import *

setup_cgi()
handler_query()
