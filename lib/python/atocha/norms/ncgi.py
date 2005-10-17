#!/usr/bin/env python
#
# $Id$
#

"""
Normalizer for Python's cgi library to handle data coming from CGI scripts.
"""

# stdlib imports.
import cgi

# atocha imports.
from atocha.norm import ArgsNormalizer
from atocha.fields.uploads import FileUpload


__all__ = ['CGINormalizer']


#-------------------------------------------------------------------------------
#
class CGINormalizer(ArgsNormalizer):
    """
    Normalizer for Python's cgi library.
    """
    def normalize( self, form ):
        args = {}
        for varname in form.keys():
            value = form[varname]

            if (isinstance(value, cgi.FieldStorage) and
                isinstance(value.file, file)):

                ovalue = FileUpload(value, value.filename)

            else:
                value = form.getlist(varname)
                if len(value) == 1:
                    ovalue = value[0]
                else:
                    ovalue = value

            args[varname] = ovalue

        return args

