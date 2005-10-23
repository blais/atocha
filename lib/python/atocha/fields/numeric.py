#!/usr/bin/env python
#
# $Id$
#

"""
Numeric Fields
"""

# stdlib imports
import locale
from types import NoneType

# atocha imports.
from atocha.field import Field, FieldError, OptRequired
from atocha.messages import msg_registry


__all__ = ['IntField', 'FloatField',]


#-------------------------------------------------------------------------------
#
class _NumericalField(Field, OptRequired):
    """
    Base class for a single-line text field that accepts and parses a numerical
    value.  The field has minimum and maximum values as well.  Classes such as
    int and float are derived from this class.

    Note: the fields derived from this field can parse 'no value' and in that
    case return None to indicate that nothing was sent by the user.
    """
    types_parse = (NoneType, unicode,)
    types_render = (unicode,)

    attributes_declare = (
        ('minval', 'int', "Minimum value that is accepted."),

        ('maxval', 'int', "Maximum value that is accepted."),

        ('format', 'str',
         """Printf-like format for output display.  If this is not set the
        default string conversion routines are used.  Note that you should set
        an appropriate format for the relevant numerical type.  Also, this does
        not affect the input parsing at all."""),
        )

    def __init__( self, name, label, attribs ):

        self.minval = attribs.pop('minval', None)
        assert isinstance(self.minval, (NoneType, self._numtype))

        self.maxval = attribs.pop('maxval', None)
        assert isinstance(self.maxval, (NoneType, self._numtype))
        
        if 'format' in attribs:
            self.format = attribs.pop('format').decode('ascii')
        else:
            self.format = None

        OptRequired.__init__(self, attribs)
        Field.__init__(self, name, label, attribs)


    def parse_value( self, pvalue ):
        # Check the required value.
        pvalue = OptRequired.parse_value(self, pvalue)

        # Unset value should be returned without checks.
        # And treat an empty string submission same as unset.
        if pvalue is None or pvalue == u'':
            return None # Indicate nothing sent by the user.

        # Otherwise try to perform the conversion and assume that the string is
        # convertible to the numerical type.
        try:
            dvalue = self._numtype(pvalue)
        except ValueError:
            raise FieldError(msg_registry['numerical-invalid'] % pvalue,
                             pvalue)

        # Check bounds.
        if self.minval is not None and dvalue < self.minval:
            rvalue = self.render_value(dvalue)
            raise FieldError(msg_registry['numerical-minval'] % rvalue, rvalue)
        if self.maxval is not None and dvalue > self.maxval:
            rvalue = self.render_value(dvalue)
            raise FieldError(msg_registry['numerical-maxval'] % rvalue, rvalue)

        return dvalue

    def render_value( self, dvalue ):
        if dvalue is None:
            return u''
        return self._format_value(dvalue)
    
    def _format_value( self, dvalue ):
        """
        Simply convert from the numerical type into a string.
        """
        if self.format:
            return self.format % dvalue
        else:
            enc = locale.getpreferredencoding()
            return str(dvalue).decode(enc)

    display_value = render_value


class IntField(_NumericalField):
    """
    A single-line text field that accepts and parses a Python integer.
    """
    types_data = (NoneType, int,)
    css_class = 'int'
    _numtype = int

    def __init__( self, name, label=None, **attribs ):
        IntField.validate_attributes(attribs)

        _NumericalField.__init__(self, name, label, attribs)


class FloatField(_NumericalField):
    """
    A single-line text field that accepts and parses a Python float.
    """
    types_data = (NoneType, float,)
    css_class = 'float'
    _numtype = float

    def __init__( self, name, label=None, **attribs ):
        FloatField.validate_attributes(attribs)

        _NumericalField.__init__(self, name, label, attribs)

