#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# $Id$
#

"""
Tests for Htmlout renderer for Atocha library.

Run these tests using the codespeak py.test tool.
"""

# stdlib imports.
import sys, os, datetime, StringIO, webbrowser
from os.path import *
from pprint import pprint, pformat

# Import the script from the demo.
sys.path.append( join(dirname(dirname(__file__)), 'demo') )
sys.path.append( join('..', 'demo') )
import common

# atocha imports.
from atocha import *

# htmlout imports.
from htmlout import tostring


#-------------------------------------------------------------------------------
#
class TestHoutRender:
    """
    Tests for rendering.
    """

    def test_simple( self ):
        "Test rendering the demo form in htmlout mode"

        r = HoutFormRenderer(common.form1)
        form = r.render()
        print tostring(form)

