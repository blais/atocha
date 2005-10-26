#!/usr/bin/env python

"""
Install script for the Atocha web forms library.
"""

__author__ = "Martin Blais <blais@furius.ca>"

import sys
from distutils.core import setup

def read_version():
    try:
        return open('VERSION', 'r').readline().strip()
    except IOError, e:
        raise SystemExit(
            "Error: you must run setup from the root directory (%s)" % str(e))

setup(name="atocha",
      version=read_version(),
      description=\
      "A web forms handling and rendering library.",
      long_description="""
Atocha is a Python library for parsing and rendering data from web forms.  It is
framework-agnostic, generic, and it should be possible to use it even with CGI
scrips or to incorporate it in your favourite web application framework
""",
      license="GPL",
      author="Martin Blais",
      author_email="blais@furius.ca",
      url="http://furius.ca/atocha",
      package_dir = {'': 'lib/python'},
      packages = ['atocha',
                  'atocha.fields',
                  'atocha.renderers',
                  'atocha.norms'],
     )
