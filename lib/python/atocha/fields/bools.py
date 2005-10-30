#!/usr/bin/env python
#
# $Id$
#

"""
Boolean Fields
"""

# stdlib imports
from types import NoneType

# atocha imports.
from atocha.field import Field, FieldError
from atocha.messages import msg_registry


__all__ = ['BoolField', 'AgreeField',]


#-------------------------------------------------------------------------------
#
class BoolField(Field):
    """
    A single boolean (checkbox) field.

    Note: this field cannot be optionally required.
    """
    types_data = (bool,)
    types_parse = (NoneType, unicode,)
    types_render = (unicode,)
    css_class = 'bool'

    attributes_declare = (
        ('disptrue', 'str', "String for display of True value."),

        ('dispfalse', 'str', "String for display of False value."),

        ('onchange', 'str (JavaScript)',
         """JavaScript to run when the field is changed. This should
         transparently render the more widely supported onclick callback."""),
        )

    def __init__( self, name, label=None, **attribs ):
        BoolField.validate_attributes(attribs)
        
        self.disptrue = attribs.pop('disptrue', None)
        self.dispfalse = attribs.pop('dispfalse', None)
        self.onchange = attribs.pop('onchange', None)

        Field.__init__(self, name, label, attribs)

    def parse_value( self, pvalue ):
        # Accept a missing argument or an empty string as False value (browsers
        # don't submit the argument for a checkbox input when it is not
        # checked).
        if pvalue is None:
            return False
        assert isinstance(pvalue, unicode)

        # Parse '0' string as False, since this is how a hidden bool field will
        # render.
        if pvalue == u'0':
            return False
        else:
            return bool(pvalue)

    def render_value( self, dvalue ):
        if dvalue is None:
            return u'0'
        if dvalue:
            return u'1'
        else:
            return u'0' # Render false.

    def display_value( self, dvalue ):
        if dvalue:
            return self.disptrue or msg_registry['display-true']
        else:
            return self.dispfalse or msg_registry['display-false']


#-------------------------------------------------------------------------------
#
class AgreeField(BoolField):
    """
    Checkbox that is required to be received, otherwise an error is given.
    """
    css_class = 'agree'

    attributes_delete = ('initial',)

    def __init__( self, name, label=None, **attribs ):
        AgreeField.validate_attributes(attribs)

        # Make sure that we're never initialized already checked (this is the
        # whole point of this field, to force the user to explicitly agree by
        # checking the checkbox).
        attribs['initial'] = False

        BoolField.__init__(self, name, label, **attribs)
        
    def isrequired( self ):
        """
        Override to place a marker that this field is required.
        Note: this field is not 'optionally required', it is ALWAYS required.
        That is its sole purpose, to force the user to sign it.
        """
        return True

    def render_value( self, dvalue ):
        # Always render False, to be accepted.
        return u'0'
    
    def parse_value( self, pvalue ):
        dvalue = BoolField.parse_value(self, pvalue)

        if dvalue is False:
            raise FieldError(msg_registry['agree-required'])

        assert dvalue is True
        return dvalue

