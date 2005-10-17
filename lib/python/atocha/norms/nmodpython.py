#!/usr/bin/env python
#
# $Id$
#

"""
Normalizer for Apache + mod_python.
"""

# stdlib imports.
import sys

# mod_python imports.
from mod_python.util import FieldStorage, Field

# atocha imports.
from atocha.norm import FormNormalizer
from atocha.fields.uploads import FileUpload


__all__ = ['ModPythonNormalizer']


#-------------------------------------------------------------------------------
#
class ModPythonNormalizer(FormNormalizer):
    """
    Normalizer for Python's cgi library.
    """
    def normalize( self, mpreq ):

        args = {}
        fs = FieldStorage(mpreq)

        # Cast down from the FieldStorage object to Python str.
        for name in fs.keys():
            value = fs[name]
            if isinstance(value, str):
                value = str(value)

            elif isinstance(value, Field):
                value = FileUpload(value)

            elif isinstance(value, list):
                for i in range(len(value)):
                    if isinstance(value[i], str):
                        value[i] = str(value[i])

                    elif isinstance(value[i], Field):
                        value[i] = FileUpload(value[i])

            if name:  # mod_python sometimes gives a None key
                args[name] = value

        return args

