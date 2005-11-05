#!/usr/bin/env python
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
Extra fields

Extra fields, which may carry meaning in certain contexts only.
"""

# stdlib imports
import re

# atocha imports.
from atocha.field import Field, FieldError
from atocha.fields.texts import StringField
from atocha.messages import msg_registry


__all__ = ['URLPathField', 'PhoneField']


#-------------------------------------------------------------------------------
#
class URLPathField(StringField):
    """
    A valid URL path.

    This is mostly used to accept return addresses in handlers.  This is always
    a hidden field.
    """

    types_data = (str,)
    css_class = 'urlpath'

    attributes_delete = ('encoding', 'strip', 'minlen', 'maxlen')

    render_as = StringField
    
    __urlpath_re = re.compile('[/a-zA-Z0-9]+$')

    def __init__( self, name, **attribs ):
        URLPathField.validate_attributes(attribs)

        attribs['encoding'] = 'ascii'
        attribs['strip'] = True
        attribs['state'] = Field.HIDDEN
        StringField.__init__(self, name, None, **attribs)

    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)
        assert isinstance(dvalue, str)

        # Check for embedded spaces.
        if not self.__urlpath_re.match(dvalue):
            raise FieldError(msg_registry['url-path-invalid'],
                             self.render_value(dvalue.replace(' ', '?')))

        return dvalue


#-------------------------------------------------------------------------------
#
class PhoneField(StringField):
    """
    A valid URL path.

    This is mostly used to accept return addresses in handlers.  This is always
    a hidden field.
    """

    types_data = (str,)
    css_class = 'phone'

    attributes_delete = ('encoding', 'strip', 'minlen', 'maxlen')

    render_as = StringField
    
    __valid_re = re.compile('^[0-9\-\.\+\(\)\ ext]+$')

    def __init__( self, name, label=None, **attribs ):
        PhoneField.validate_attributes(attribs)

        attribs['encoding'] = 'ascii'
        attribs['strip'] = True
        StringField.__init__(self, name, label, **attribs)

    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)
        assert isinstance(dvalue, str)

        # Check for embedded spaces.
        if dvalue and not self.__valid_re.match(dvalue):
            raise FieldError(msg_registry['phone-invalid'] % dvalue,
                             self.render_value(dvalue))

        return dvalue

