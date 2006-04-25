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
Fields for usernames
"""

# stdlib imports
import re

# atocha imports
from atocha.field import FieldError
from atocha.fields.texts import StringField, EmailField
from atocha.messages import msg_registry


__all__ = ['UsernameField', 'UsernameOrEmailField']


#-------------------------------------------------------------------------------
#
class UsernameField(StringField):
    """
    Username field with a maximum length and which automatically lowercases the
    parsed value.
    """

    attributes_declare = (
        ('autolower', 'bool',
         """Determines whether we automatically convert the given name to
         lowercase, or raise an error if some uppercase characters were found.
         """),
        )

    attributes_delete = ('encoding', 'strip')

    render_as = StringField
    
    # Defaults for lengths limits.
    _default_minlen = 3
    _default_maxlen = 16

    # Simple usernames.
    __username_re = re.compile('[a-z0-9]*')

    def __init__( self, name, label=None, **attribs ):
        UsernameField.validate_attributes(attribs)

        self.autolower = attribs.pop('autolower', False)

        if 'minlen' not in attribs:
            attribs['minlen'] = self._default_minlen
        if 'maxlen' not in attribs:
            attribs['maxlen'] = self._default_maxlen

        if label is None:
            label = msg_registry['username-label']

        attribs['encoding'] = 'ascii'
        attribs['strip'] = True

        StringField.__init__(self, name, label, **attribs)
        
    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)

        dvalue = UsernameField.validate_username(dvalue, self.autolower)

        return dvalue

    def validate_username( dvalue, autolower ):
        """
        Validate the the value is an acceptable username.
        """
        # Raise error if the name is not lowercase.
        dvalue_low = dvalue.lower()
        if dvalue_low != dvalue:
            if autolower:
                dvalue = dvalue_low
            else:
                raise FieldError(msg_registry['username-lower-error'],
                                 dvalue_low.decode('ascii', 'replace'))

        # Check against regexp.
        if not UsernameField.__username_re.match(dvalue):
            raise FieldError(msg_registry['username-lower-error'],
                             dvalue.decode('ascii', 'replace'))
        
        return dvalue
    
    validate_username = staticmethod(validate_username)


#-------------------------------------------------------------------------------
#
class UsernameOrEmailField(EmailField):
    """
    A field that can accept either a username or an email address.
    """

    attributes_delete = ('accept_local',)

    render_as = StringField # Always render just as a string.

    def __init__( self, name, label=None, **attribs ):
        UsernameOrEmailField.validate_attributes(attribs)

        attribs['accept_local'] = True

        if label is None:
            label = msg_registry['username-or-email-label']

        EmailField.__init__(self, name, label, **attribs)
        
    def parse_value( self, pvalue ):
        # Note: this always works, even for usernames, because we accept local
        # emails.
        dvalue = EmailField.parse_value(self, pvalue)

        # Check if the value is a user-id or email address.
        if '@' not in dvalue:
            # It's a username, validate for usernames.
            #
            # By default, auto-lower, because this field will never be used to
            # register, and we want to make the user's life as easy as possible.
            dvalue = UsernameField.validate_username(dvalue, autolower=True)

        return dvalue

