#!/usr/bin/env python
#
# $Id$
#

"""
Fields for usernames
"""

# stdlib imports
import re

# atocha imports.
from atocha.field import Field, FieldError
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

        UsernameField.validate_username(dvalue)

        return dvalue

    def validate_username( dvalue ):
        """
        Validate the the value is an acceptable username.
        """
        # Raise error if the name is not lowercase.
        dvalue_low = dvalue.lower()
        if dvalue_low != dvalue:
            if self.autolower:
                dvalue = dvalue_low
            else:
                raise FieldError(msg_registry['username-lower-error'],
                                 dvalue_low)

        # Check against regexp.
        if not UsernameField.__username_re.match(dvalue):
            raise FieldError(msg_registry['username-lower-error'], dvalue)
        
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
            UsernameField.validate_username(dvalue)

        return dvalue

