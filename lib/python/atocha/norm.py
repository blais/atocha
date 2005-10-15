#!/usr/bin/env python
#
# $Id$
#

"""
Argument normalization classes.

These classes are used to convert between the various formats for the arguments
that the different web frameworks or libraries provide.  The arguments are
normalized first, without any knowledge of the form in which they will get
parsed, and then returned for parsing.
"""


# stdlib imports.
import sys, cgi

# atocha imports.
from fields.uploads import FileUpload


__all__ = ['CGINormalizer']


#-------------------------------------------------------------------------------
#
class FormNormalizer:
    """
    Base interface for normalizers.
    """
    def normalize( self, submitted_args ):
        """
        Normalize the submitted arguments and return a dict with the normalized
        arguments for parsing.
        """
        raise NotImplementedError

#-------------------------------------------------------------------------------
#
class CGINormalizer(FormNormalizer):
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

