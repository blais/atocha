#!/usr/bin/env python
#
# $Id$
#

"""
Fields ...
"""

# stdlib imports
from types import NoneType

# atocha imports.
from atocha.field import Field, FieldError
from atocha.messages import msg_registry


__all__ = ['BoolField',]


#-------------------------------------------------------------------------------
#
class BoolField(Field):
    """
    A single boolean (checkbox) field.

    Note: this field cannot be optionally required.
    """
    types_data = (bool,)
    types_parse = (NoneType, unicode,)
    types_render = (bool,)
    css_class = 'bool'

    def __init__( self, name,
                  label=None, hidden=None, initial=None,
                  disptrue=None, dispfalse=None ):
        Field.__init__(self, name, label, hidden, initial)

        self.disptrue = disptrue
        self.dispfalse = dispfalse
        """String for display.  This can be a useful convenience."""

    def parse_value( self, pvalue ):
        # Accept a missing argument or an empty string as False value (browsers
        # don't submit the argument for a checkbox input when it is not
        # checked).
        return bool(pvalue is not None and pvalue)

    def render_value( self, dvalue ):
        if dvalue is None:
            return False
        return dvalue

    def display_value( self, dvalue ):
        if dvalue:
            return self.disptrue or msg_registry['display-true']
        else:
            return self.dispfalse or msg_registry['display-false']

