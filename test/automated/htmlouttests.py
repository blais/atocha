#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# $Id$
#
#  Atocha -- A web forms rendering and handling Python library.
#  Copyright (C) 2005  Martin Blais
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
Tests for Htmlout renderer for Atocha library.

Run these tests using the codespeak py.test tool.
"""

# stdlib imports
import sys, os, datetime, StringIO, webbrowser
from os.path import *
from pprint import pprint, pformat

# Import the script from the demo.
sys.path.append( join(dirname(dirname(__file__)), 'demo') )
sys.path.append( join('..', 'demo') )
import common

# atocha imports
from atocha import *

# htmlout imports
from htmlout import tostring



class TestHoutRender:
    """
    Tests for rendering.
    """

    def test_simple(self):
        "Test rendering the demo form in htmlout mode"

        r = HoutFormRenderer(common.form1)
        form = r.render()
        print tostring(form)

