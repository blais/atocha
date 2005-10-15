#!/usr/bin/env python
#
# $Id$
#

"""
Fields ...
"""

# stdlib imports
import re, email.Utils
from types import NoneType

# atocha imports.
from atocha.field import Field, FieldError, OptRequired
from atocha.messages import msg_registry


__all__ = ['StringField', 'TextAreaField', 'PasswordField',
           'EmailField', 'URLField',]


#-------------------------------------------------------------------------------
#
class _TextField(Field, OptRequired):
    """
    Base class for fields receiving text.

    Additional attributes:

    - 'minlen': Minimal length of text field.

    - 'maxlen': Maximal length of text field.

    - 'encoding': Which encoding is considered to be a valid parsed/data value
                  for this field. If you leave this to None, the field produces
                  Unicode values.

    """
    types_data = (str, unicode,)
    types_parse = (NoneType, unicode,)
    types_render = (unicode,)
    css_class = 'text'

    def __init__( self, name,
                  label=None, hidden=None, initial=None, required=None,
                  minlen=None, maxlen=None, encoding=None ):
        Field.__init__(self, name, label, hidden, initial)
        OptRequired.__init__(self, required)

        self.minlen = minlen
        "Minimum length of the field."

        self.maxlen = maxlen
        "Maximum  length of the field."

        self.encoding = encoding
        "Encoding to convert the string into and to validate."

    def parse_value( self, pvalue ):
        # Check the required value.
        pvalue = OptRequired.parse_value(self, pvalue)

        # If the value is not sent, return an empty value.
        #
        # A field that has a minimal value option will trigger an error if it is
        # not set at all.  We could make that optional in the future.  The
        # minimal length check below will trigger an error.
        if pvalue is None:
            pvalue = u''

        # Convert the data value to the specified encoding if requested.
        if self.encoding is not None:
            try:
                dvalue = pvalue.encode(self.encoding)
            except UnicodeEncodeError:
                # Encode a string for the proper encoding that will still be
                # printable but with the offending chars replaced with
                # something.
                if self.encoding:
                    rvalue = pvalue.encode(
                        self.encoding, 'replace').decode(self.encoding)
                else:
                    rvalue = pvalue
                raise FieldError(msg_registry['text-invalid-chars'], rvalue)
        else:
            # Otherwise we simply use the unicode value.
            dvalue = pvalue

        # Check the minimum and maximum lengths.
        if self.minlen is not None and self.minlen > len(dvalue):
            raise FieldError(msg_registry['text-minlen'],
                             self.render_value(dvalue))
        if self.maxlen is not None and len(dvalue) > self.maxlen:
            raise FieldError(msg_registry['text-maxlen'],
                             self.render_value(dvalue))

        # Make sure that the value does not contain control chars.
        v, dvalue_chars = None, []
        for ch in dvalue:
            o = ord(ch)
            if o < 0x20 and o != 10 and o != 13:
                v = FieldError(msg_registry['text-invalid-chars'])
            else:
                # We're also building a clean version of the string for
                # rendering back when the error returns.
                dvalue_chars.append(ch)
        if self.encoding is None:
            dvalue_clean = u''.join(dvalue_chars)
        else:
            dvalue_clean = ''.join(dvalue_chars)
        if v is not None:
            v.args = v.args + (dvalue_clean,)
            raise v

        # Return the parsed valid value.
        return dvalue

    def render_value( self, dvalue ):
        if dvalue is None:
            return u''
        return _TextField.display_value(self, dvalue)

    def display_value( self, dvalue ):
        if self.encoding is not None:
            assert isinstance(dvalue, str)
            # Convert the data value to a unicode object for rendering.
            rvalue = dvalue.decode(self.encoding)
        else:
            assert isinstance(dvalue, unicode)
            rvalue = dvalue
        return rvalue


#-------------------------------------------------------------------------------
#
class StringField(_TextField):
    """
    String input that must be on a single line.

    Additional attributes:

    - 'strip': Whether the data string returned has whitespace automatically
      stripped off the beginning and end of it.
    """
    css_class = 'string'

    def __init__( self, name,
                  label=None, hidden=None, initial=None, required=None,
                  minlen=None, maxlen=None, size=None, encoding=None,
                  strip=False ):
        _TextField.__init__(self, name, label, hidden, initial, required,
                            minlen, maxlen, encoding)

        self.size = size or maxlen
        """Suggested rendering size of the field."""

        self.strip = strip
        """Whether the string should be stripped before rendering and during
        parsing."""

    def parse_value( self, pvalue ):
        dvalue = _TextField.parse_value(self, pvalue)

        # Check that the value contains no newlines.
        if ((isinstance(dvalue, unicode) and
             (u'\n' in dvalue or u'\r' in dvalue)) or
            (isinstance(dvalue, str) and
             ('\n' in dvalue or '\r' in dvalue))):

            raise FieldError(msg_registry['text-invalid-chars'],
                             self.render_value(dvalue))

        if self.strip:
            # Strip the parsed valid text value.
            return dvalue.strip()
        else:
            return dvalue

    def render_value( self, dvalue ):
        rvalue = _TextField.render_value(self, dvalue)

        # Strip the value on rendering as well, if necessary.
        if self.strip:
            return rvalue.strip()
        else:
            return rvalue

#-------------------------------------------------------------------------------
#
class TextAreaField(_TextField):
    """
    A multi-line string.
    """
    css_class = 'textarea'

    def __init__( self, name,
                  label=None, hidden=None, initial=None, required=None,
                  minlen=None, maxlen=None, encoding=None,
                  rows=None, cols=None ):
        _TextField.__init__(self, name, label, hidden, initial, required,
                            minlen, maxlen, encoding)

        self.rows = rows
        "The number of rows to render the field with."

        self.cols = cols
        "The number of columns to render the field with."

    def render_value( self, dvalue ):
        rvalue = _TextField.render_value(self, dvalue)

        if self.encoding:
            # Make sure the DOS CR-LF are converted into simple Unix newlines
            # for the browser, in case some data value is set wrongly.
            return rvalue.replace('\r\n', '\n')
        else:
            return rvalue.replace(u'\r\n', u'\n')

    display_value = render_value


#-------------------------------------------------------------------------------
#
class PasswordField(StringField):
    """
    A single-line field for entering a password.

    When rendering, optionally, we don't output the password back into HTML, to
    avoid disclosure over unencrypted communication channels.
    """
    css_class = 'password'

    def __init__( self, name,
                  label=None, hidden=None, initial=None, required=None,
                  minlen=None, maxlen=None, size=None, encoding=None,
                  hidepw=True ):
        StringField.__init__(self, name, label, hidden, initial, required,
                             minlen, maxlen, size, encoding, strip=False)

        self.hidepw = hidepw
        "Specifies whether the password should be hidden on rendering."

    def render_value( self, dvalue ):
        if self.hidepw:
            return u''
        else:
            return _TextField.render_value(self, dvalue)

    def display_value( self, dvalue ):
        # Never display passwords in any case ever!
        return u'*' * len(dvalue)



#-------------------------------------------------------------------------------
#
class EmailField(StringField):
    """
    Field for an email address.  The user can enter a full name with <> but the
    name is automatically thrown away.

    Encoding is fixed to 'ascii', data is stripped automatically.
    """
    types_data = (str,)
    css_class = 'email'

    __email_re = re.compile('^.*@.*\.[a-zA-Z][a-zA-Z]+$')

    def __init__( self, name, label=None, hidden=None,
                  initial=None, required=None, accept_local=False ):
        StringField.__init__(self, name, label, hidden, initial, required,
                             size=None, encoding='ascii', strip=True)

        self.accept_local = accept_local
        """True if we accept local email addresses (i.e. without a @)."""

    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)
        assert isinstance(dvalue, str)

        # Accept an empty string as a valid value for email address.
        if not dvalue:
            return dvalue

        # Parse the email address using the appropriate Python module.
        name, addr = email.Utils.parseaddr(dvalue)
        if not addr:
            raise FieldError(msg_registry['email-invalid'],
                             self.render_value(dvalue))
        else:
            # Check for local addresses.
            if not self.accept_local and not EmailField.__email_re.match(addr):
                raise FieldError(msg_registry['email-invalid'],
                                 self.render_value(dvalue))
                # Note: if we had a little more guts, we would remove the
                # offending characters in the replacement value.

            # We throw away the name of the person and just keep the actual
            # email address part.
            return addr

    def render_value( self, dvalue ):
        # Mangle the @ character into an HTML equivalent.
        # dvalue.replace('@', '&#64;')
        # Note: disabled, until we can find a nice way to output this without
        # escaping in htmlout.
        return StringField.render_value(self, dvalue)

    def display_value( self, dvalue ):
        # Mangle the @ character into an HTML equivalent.
        # dvalue.replace('@', '&#64;')
        # Note: disabled, until we can find a nice way to output this without
        # escaping in htmlout.
        return StringField.render_value(self, dvalue)

#-------------------------------------------------------------------------------
#
class URLField(StringField):
    """
    Field for an URL. We can parse some of the syntax for a valid URL.  This
    field can also be used by the renderer to automatically add a link to the
    displayed value, if it is requested to render for display only.

    Encoding is fixed to 'ascii', data is stripped automatically.
    """
    types_data = (str,)
    css_class = 'url'

    def __init__( self, name, label=None, hidden=None,
                  initial=None, required=None ):
        StringField.__init__(self, name, label, hidden, initial, required,
                             size=None, encoding='ascii', strip=True)

    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)
        assert isinstance(dvalue, str)

        # Check for embedded spaces.
        if ' ' in dvalue:
            raise FieldError(msg_registry['url-invalid'],
                             self.render_value(dvalue.replace(' ', '?')))

        # Note: eventually, we want to parse using urlparse or something.

        return dvalue
