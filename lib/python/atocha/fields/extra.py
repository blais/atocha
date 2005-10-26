#!/usr/bin/env python
#
# $Id$
#

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


__all__ = ['URLPathField']


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

    render_as = StringField  # Won't be used much anyway.
    
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
        if not __urlpath_re.match(dvalue):
            raise FieldError(msg_registry['url-path-invalid'],
                             self.render_value(dvalue.replace(' ', '?')))

        return dvalue

