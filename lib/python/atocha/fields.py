#!/usr/bin/env python
#
# $Id$
#

"""
Form fields (widgets) definitions.
"""

# stdlib imports
import sys, types, re, datetime, StringIO, email.Utils
if sys.version_info[:2] < (2, 4):
    from sets import Set as set

# atocha imports.
from messages import msg_registry, msg_type



__all__ = [
    'Field',
    'StringField', 'TextAreaField', 'DateField', 'EmailField', 'URLField',
    'IntField', 'FloatField', 'BoolField',
    'RadioField', 'MenuField', 'CheckboxesField', 'ListboxField',
    'JSDateField',
    'FileUploadField',
    ]


#-------------------------------------------------------------------------------
#
class Field:
    """
    Common class for all form fields.

    This class defines all the common attributes of various form input fields.
    Instances of subclasses are added to a Form object to define a specific set
    of inputs, which can be used to render and parse/handle a submission of this
    form.  Each field must be given at least a name, which should unique within
    the form.

    Fields:

    - 'name': Unique identifier for the field, and name of the form variables as
      well;

    - 'label' (optional): Label that is used to identify the field when
      rendering it.

    - 'hidden' (optional): the field is rendered as a hidden input and does not
      show up visibly in the browser page;

    - 'initial': Default value that is used for rendering the field with known
      initial conditions if no value is given for it.  Important note: this
      value is not used by the parsing at all.  If an argument is missing during
      parsing, the value associated with the field will be set to None.

    Types: every field class should define the following class attributes:

    - 'types_data' -> tuple: possible data types for parsed values.
    - 'types_parse' -> tuple: possible types of input of parsing method.
    - 'types_render' -> tuple: possible types for prepared values for rendering.

    Important note about usage of required fields
    ---------------------------------------------

    One issue is what to expect from the browsers, in terms of the values
    getting submitted for parsing.  If a field gets parsed, and it gets no
    value, we are assuming that the user did not fill the field in.

    The problem is that if a field is disabled by some DHTML or Javascript, its
    value will not get submitted, but we assume that the callers will take care
    of not invoking the parsing on fields which might have been disabled (using
    the 'only' and 'ignore' keywords of the FormParser parsing methods).  This
    is the only way that we can insure constraints for the _OneChoiceField
    class, for which the value is implicitly required.

    Basically, if the field can be disabled, you need to make sure when you use
    the FormParser that you do not inadvertently invoke parsing on these fields
    until you are sure--by check the value of your other fields, correlating
    them with your GUI code-- that they were not disabled.

    This means that parsing the results of a form which has some complex widget
    hiding interactions will be a little more complicated.  However, this buys
    us the possibility of having widgets for which we can insure that at least
    one value has been submitted (radio buttons, required listboxes).
    """
    
    # Regular expression for valid variable names.
    varname_re = re.compile('[a-z0-9]')

    def __init__( self, name, label=None, hidden=None, initial=None ):
        assert isinstance(name, str)
        assert isinstance(label, (type(None), msg_type))
        assert isinstance(initial, (type(None), bool, int))
        assert isinstance(hidden, (type(None), bool, int))

        self.name = name
        "Name of the field."

        assert Field.varname_re.match(name)
        self.varname = name
        """Name of the variable used for the field, by default, the same name
        as the field itself."""

        self.label = label
        "The visible label used by the form rendering."

        self.hidden = hidden or False
        "Whether the field is to be rendered as hidden or not."

        # Make sure that the initial value is of an acceptable type for this
        # field.
        assert isinstance(initial, (type(None),) + self.types_data)
        self.initial = initial
        """The initial value set on the field when rendering, if not provided
        by the values array."""

    def __str__( self ):
        """
        Returns a human-readable version of the field.
        """
        return "<Field name=%s>" % self.name

    def ishidden( self ):
        """
        Returns true if this field is hidden.
        """
        return self.hidden

    def isrequired( self ):
        """
        Returns whether this field is required (optionally or not) or not.
        This is meant to be used exclusively for rendering purpose (e.g. to
        put some kind of indicator in the output that the user has to fill
        in certain values).

        There is a subtletly about this that you must be aware: optionally
        required fields can be required, other fields cannot.  See class
        _OptRequired for more details.
        """
        try:
            isreq = getattr(self, 'required')
        except AttributeError:
            isreq = False
        return isreq

    def parse_value( self, pvalue ):
        """
        Convert the value coming from the browser into the data value.  The
        value from the browser is already decoded at the form parsing level and
        so 'pvalue' strings or strings contained within lists are actually
        already given as unicode objects.

        If there is an error in parsing, DUE TO OUTPUT THAT THE USER MAY HAVE
        ENTERED, the protocol is to raise a ValueError, initialized with an
        message that indicates what the error and a 'dvalue' (of one of the
        valid data-types for the field) that be used to render the field back
        with the invalid value when re-rendering.  This value may optionally be
        corrected as well.

        (Note that if there is an unexpected value, which is NOT DUE TO USER
        INPUT, you should not raise a ValueError, but rathre fail with an assert
        or a RuntimeError.)
        """
        raise NotImplementedError # return dvalue

    def render_value( self, dvalue ):
        """
        Prepare the data value for rendering as part of a form rendering for an
        HTML input widget.  This is not meant for displayin the value read-only
        to the user (see other method to do that).  This will generally involve
        a type change, but may also implement other kinds of preparation.  The
        renderer classes are expected to know how to deal with the particular
        types to be rendered for each of the field types.
        """
        raise NotImplementedError # return rvalue




#------------------------------------------------------------------------------
#
class _OptRequired:
    """
    Base class for all fields which can be optionally required, that is, which
    can take the 'required' option which allows them to check whether the input
    was submitted or not.

    The required field is checked via the parse_value() method for each field
    type, and not in the parser itself (previous versions of this library used
    to do that).
    """
    def __init__( self, required=None ):
        """
        :Arguments:

        - 'required': Indicates that if the value is missing from the arguments
          during parsing, and error will be signaled for that input.  If
          'required' is not set, a missing argument will produce a value of
          None in the parser for the corresponding field.

          Important note: the 'required' option does not make sense for all the
          field types, due to the nature of the submission protocol (for
          example, for the checkboxes, the absence of the field value means a
          value of False, so we cannot really check if the value was False or
          ''not submitted''.  This is why some of the fields do not support the
          required field.

        """
        assert isinstance(required, (type(None), bool, int))
        self.required = required
        "Whether the argument is OPTIONALLY required or not."

    def parse_value( self, pvalue ):
        """
        Check that the field is present.  Fields which derive from this one do
        not accept None if the value is required.
        """
        if self.required and pvalue is None or pvalue == u'' or pvalue == []:
            # We indicate an error mentioning that this field was required.
            raise ValueError(msg_registry['error-required-value'], None)

        return pvalue

#-------------------------------------------------------------------------------
#
class _TextField(Field, _OptRequired):
    """
    Base class for fields receiving text.

    Additional attributes:

    - 'minlen': Minimal length of text field.

    - 'maxlen': Maximal length of text field.

    - 'encoding': Which encoding is considered to be a valid parsed/data value
                  for this field. If you leave this to None, the field produces
                  Unicode values.

    """
    types_data = (str, unicode, type(None))
    types_parse = (type(None), unicode,)
    types_render = (unicode,)
    css_class = 'text'

    def __init__( self, name,
                  label=None, hidden=None, initial=None, required=None,
                  minlen=None, maxlen=None, encoding=None ):
        Field.__init__(self, name, label, hidden, initial)
        _OptRequired.__init__(self, required)

        self.minlen = minlen
        "Minimum length of the field."

        self.maxlen = maxlen
        "Maximum  length of the field."

        self.encoding = encoding
        "Encoding to convert the string into and to validate."

    def parse_value( self, pvalue ):
        # Check the required value.
        pvalue = _OptRequired.parse_value(self, pvalue)

        # If the value is not required and not given to us, return unparsed
        # value.
        #
        # Note: a field can have a minimal value, but still be unsent (if it is
        # not required) and if that happens the minimal length will not trigger
        # an error.
        if pvalue is None:
            return None

        # Convert the data value to the specified encoding if requested.
        if self.encoding is not None:
            try:
                dvalue = pvalue.encode(self.encoding)
            except UnicodeEncodeError:
                # Encode a string for the proper encoding that will still be
                # printable but with the offending chars replaced with
                # something.
                dvalue = pvalue.encode(self.encoding, 'replace')
                raise ValueError(msg_registry['text-invalid-chars'], dvalue)
        else:
            # Otherwise we simply use the unicode value.
            dvalue = pvalue

        # Check the minimum and maximum lengths.
        if self.minlen is not None and self.minlen > len(dvalue):
            raise ValueError(msg_registry['text-minlen'], dvalue)
        if self.maxlen is not None and len(dvalue) > self.maxlen:
            raise ValueError(msg_registry['text-maxlen'], dvalue)

        # Make sure that the value does not contain control chars.
        v, dvalue_chars = None, []
        for ch in dvalue:
            o = ord(ch)
            if o < 0x20 and o != 10:
                v = ValueError(msg_registry['text-invalid-chars'])
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
                  minlen=None, maxlen=None, encoding=None,
                  strip=False ):
        _TextField.__init__(self, name, label, hidden, initial, required,
                            minlen, maxlen, encoding)

        self.strip = strip
        """Whether the string should be stripped before rendering and during
        parsing."""

    def parse_value( self, pvalue ):
        dvalue = _TextField.parse_value(self, pvalue)

        # Unset value should be returned without checks.
        if dvalue is None:
            return None

        # Check that the value contains no newlines.
        if '\n' in dvalue or '\r' in dvalue:
            raise ValueError(msg_registry['text-invalid-chars'], dvalue)

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

        # Make sure the DOS CR-LF are converted into simple Unix newlines for
        # the browser, in case some data value is set wrongly.
        return rvalue.replace('\r\n', '\n')


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
                  minlen=None, maxlen=None, encoding=None, hidepw=True ):
        StringField.__init__(self, name, label, hidden, initial, required,
                             minlen, maxlen, encoding, strip=False)

        self.hidepw = hidepw
        "Specifies whether the password should be hidden on rendering."

    def render_value( self, dvalue ):
        if self.hidepw:
            return u''
        else:
            return _TextField.render_value(self, dvalue)


#-------------------------------------------------------------------------------
#
class DateField(StringField):
    """
    A string field that accepts strings that represent dates, in some specific
    formats.
    """
    types_data = (type(None), datetime.date,)
    types_parse = (type(None), unicode,)
    types_render = (unicode,)
    css_class = 'date'

    # Note: for now, we only support iso-8601 format.  When this becomes
    # necessary, some more improvements could be done here.
    __date_re = re.compile('(\d\d\d\d)-(\d\d)-(\d\d)')

    def __init__( self, name, label=None, hidden=None,
                  initial=None, required=None ):
        StringField.__init__(self, name, label, hidden,
                             initial, required, strip=True)

    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)

        # Unset value should be returned without more checks.
        if dvalue is None:
            return None

        # Check that the value matches our format.
        mo = self.__date_re.match(dvalue)
        if not mo:
            raise ValueError(
                msg_registry['date-invalid-format'] % dvalue, None)

        # Convert into date.
        try:
            dvalue = datetime.date(*map(int, mo.groups()))
        except ValueError, e:
            raise ValueError(msg_registry['date-invalid'] % dvalue, None)

        return dvalue

    def render_value( self, dvalue ):
        # Convert the date object in a format suitable for rendering it.
        rvalue = unicode(dvalue.isoformat())
        return rvalue

#-------------------------------------------------------------------------------
#
class EmailField(StringField):
    """
    Field for an email address.  The user can enter a full name with <> but the
    name is automatically thrown away.

    Encoding is fixed to 'ascii', data is stripped automatically.
    """
    types_data = (str, type(None))
    css_class = 'email'

    def __init__( self, name, label=None, hidden=None,
                  initial=None, required=None, accept_local=False ):
        StringField.__init__(self, name, label, hidden, initial, required,
                             encoding='ascii', strip=True)

        self.accept_local = accept_local
        """True if we accept local email addresses (i.e. without a @)."""

    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)
        assert isinstance(dvalue, (type(None), str))

        # Unset value should be returned without checks.
        if dvalue is None:
            return None

        # Parse the email address using the appropriate Python module.
        name, addr = email.Utils.parseaddr(dvalue)
        if (name, addr) == ('', ''):
            raise ValueError(msg_registry['email-invalid'], dvalue)
        else:
            # Check for local addresses.
            if not self.accept_local and '@' not in addr:
                raise ValueError(msg_registry['email-invalid'], dvalue)
                # Note: if we had a little more balls, we would remove the
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

#-------------------------------------------------------------------------------
#
class URLField(StringField):
    """
    Field for an URL. We can parse some of the syntax for a valid URL.  This
    field can also be used by the renderer to automatically add a link to the
    displayed value, if it is requested to render for display only.

    Encoding is fixed to 'ascii', data is stripped automatically.
    """
    types_data = (str, type(None))
    css_class = 'url'

    def __init__( self, name, label=None, hidden=None,
                  initial=None, required=None ):
        StringField.__init__(self, name, label, hidden, initial, required,
                             encoding='ascii', strip=True)

    def parse_value( self, pvalue ):
        dvalue = StringField.parse_value(self, pvalue)
        assert isinstance(dvalue, (type(None), str))

        # Unset value should be returned without checks.
        if dvalue is None:
            return None

        # Check for embedded spaces.
        if ' ' in dvalue:
            raise ValueError(msg_registry['url-invalid'],
                             dvalue.replace(' ', '?'))

        # Note: eventually, we want to parse using urlparse or something.

        return dvalue

#-------------------------------------------------------------------------------
#
class _NumericalField(Field, _OptRequired):
    """
    Base class for a single-line text field that accepts and parses a numerical
    value.  The field has minimum and maximum values as well.  Classes such as
    int and float are derived from this class.
    """
    types_parse = (type(None), unicode,)
    types_render = (unicode,)

    def __init__( self, name,
                  label=None, hidden=None, initial=None, required=None,
                  minval=None, maxval=None ):
        Field.__init__(self, name, label, hidden, initial)
        _OptRequired.__init__(self, required)

        assert isinstance(minval, (type(None), self._numtype))
        assert isinstance(maxval, (type(None), self._numtype))

        self.minval = minval
        "Minimum value that is accepted."

        self.maxval = maxval
        "Maximum value that is accepted."

    def parse_value( self, pvalue ):
        # Check the required value.
        pvalue = _OptRequired.parse_value(self, pvalue)

        # Unset value should be returned without checks.
        if pvalue is None:
            return None

        # Treat an empty string submission same as unset.
        if pvalue == u'':
            return None

        # Otherwise try to perform the conversion and assume that the string is
        # convertible to the numerical type.
        try:
            dvalue = self._numtype(pvalue)
        except ValueError:
            raise ValueError(msg_registry['numerical-invalid'], None)

        # Check bounds.
        if self.minval is not None and dvalue < self.minval:
            raise ValueError(msg_registry['numerical-minval'] % self.minval,
                             dvalue)
        if self.maxval is not None and dvalue > self.maxval:
            raise ValueError(msg_registry['numerical-maxval'] % self.maxval,
                             dvalue)

        return dvalue

    def render_value( self, dvalue ):
        # Simply convert from the numerical type into a string.
        return unicode(dvalue)


class IntField(_NumericalField):
    """
    A single-line text field that accepts and parses a Python integer.
    """
    types_data = (int, type(None))
    css_class = 'int'
    _numtype = int


class FloatField(_NumericalField):
    """
    A single-line text field that accepts and parses a Python float.
    """
    types_data = (float, type(None))
    css_class = 'float'
    _numtype = float


#-------------------------------------------------------------------------------
#
class BoolField(Field): # Cannot be optionally required.
    """
    A single boolean (checkbox) field.

    Note: this field cannot be required.
    """
    types_data = (bool,)
    types_parse = (type(None), unicode,)
    types_render = (unicode,)
    css_class = 'bool'

    def parse_value( self, pvalue ):
        # Accept a missing argument or an empty string as False value (browsers
        # don't submit the argument for a checkbox input when it is not
        # checked).
        return bool(pvalue is not None and pvalue)

    def render_value( self, dvalue ):
        # We convert the value to an int to show up appropriately in the input.
        return dvalue and u'1' or u'0'


#-------------------------------------------------------------------------------
#
class _MultipleField(Field):
    """
    Base class for fields that allow zero, one or multiple choices among many.
    It contains the interface and abitilities for a being set a list of values
    to labels.  This is a base class for radio buttons, lists of checkboxes and
    menus.

    The values are ascii str's only, they cannot be unicode (this is a
    limitation we impose ourselves, as a recognition that the values are to be
    used internally only, and not as user-visible strings).

    One issue with the choices fields is that the set of valid values may be
    generated dynamically, and therefore sometimes we need to be able to create
    the field at a moment where we do not know in advance what the values will
    be.  If this is the case:

    - for rendering: we set the values on the field right before rendering it.

    - for parsing: the field has an option to avoid checking against values set
      on it.  You can set that field and then do some manual checking using the
      protocol provided by the form parser.

    See the concrete fields for an explanation of the kinds of parsing input
    that they can accept, and how they deal with them.
    """
    types_parse = (type(None), list,)
    types_render = (list,)

    def __init__( self, name, values,
                  label=None, hidden=None, initial=None, nocheck=None ):
        """
        :Arguments:

        - 'values': See setvalues() for full description.

        - 'nocheck' -> bool: Set this to True if you want to prevent the parser
          from cross-checking against the values set in the instance of this
          field.

        """
        Field.__init__(self, name, label, hidden, initial)

        self.nocheck = nocheck
        """When parsing, do not perform checks specific to the values set on
        against the received values. This is useful if the set of values for
        this field is generated dynamically and you will do your validation by
        hand.  Another thing that can be done is to not use this but to call
        setvalue() before running the parser on the arguments, if in the
        handler you know which values are possibly valid and would like to use
        the parsing code provided in this field."""

        self.values = None
        "(Internal use only.) List of the possible values for this field"

        self.valueset = None
        """(Internal use only.) Set of the possible values for this field,
        maintainde for fast lookup only."""

        # Set the initial values for this field.
        self.setvalues(values)


    def setvalues( self, values ):
        """
        Set the values that this field renders and parses.  'values' is of the
        same types as described in the constructor.

        :Arguments:

        - 'values' -> list or tuple of str or (str, unicode) value-label pairs:
          the ordered values, to be rendered and checked against when parsing.
          This is not a mapping because order is important for rendering.  If
          the elements of the list are pairs, the label is used for the
          user-visible strings to be used when rendering the widget.

          Note that we also accept integers for values instead of ascii
          strings, but these will be automatically converted to strings.

        """
        self.valueset = set()
        self.values = []

        # Accumulator for the normalized values.
        normvalues = []

        if values is None:
            return
        else:
            assert isinstance(values, (list, tuple))

            # Normalize all the values into pairs.
            for el in values:

                value = label = None

                # Accept simple values.
                if isinstance(el, (int, str)):
                    value = el

                # And of course, a value-label pair.
                elif isinstance(el, tuple):
                    assert len(el) == 2
                    value, label = el

                else:
                    raise RuntimeError(
                        "Error: wrong type of value in initializer element: %s."
                        % type(el))

                # Convert integer value into string if necessary.
                if isinstance(value, int):
                    value = str(value)

                # If the label is not set, it takes the same value as the label
                # (convert to unicode from ascii).
                if label is None:
                    label = value.decode('ascii')
                else:
                    # Other we check to make sure that the label is of type
                    # msg_type, which is the required type for all the
                    # user-visible values.
                    assert isinstance(label, msg_type)

                # Just more zealous sanity checking.
                assert isinstance(value, str)

                # We add the new pair to our internal, normalized set of
                # values.
                self.values.append( (value, label) )
                self.valueset.add(value)


    def checkvalues( self, values ):
        """
        Cross-check values agains the set of possible values for this field.
        The 'nocheck' option is processed here internally, so you can just call
        this method in the derived classes. 'values' must be a list or tuple of
        value strings to be checked.

        This method automatically raises an exception if the values do not
        cross-check.  We return nothing.
        """
        if self.nocheck:
            return

        for value in values:
            assert isinstance(value, str)

            if value not in self.valueset:
                # Note: this could be an internal error.
                raise RuntimeError("Error: internal error checking values "
                                   "in a multiple field.")

#-------------------------------------------------------------------------------
#
class _Orientable:
    """
    Base class for fields that can be oriented.  Fields derived from this base
    class may have to be laid out horizontally or vertically.The renderers will
    most likely create a small table to lay out the radio buttons nicely, and
    this setting allows the user to choose the layout style.
    """

    ORI_VERTICAL = 1
    ORI_HORIZONTAL = 2

    def __init__( self, orient=ORI_VERTICAL ):

        assert orient in [_Orientable.ORI_VERTICAL,
                          _Orientable.ORI_HORIZONTAL]
        self.orient = orient
        """Orientation of the field for rendering."""


#-------------------------------------------------------------------------------
#
class _OneChoiceField(_MultipleField):
    """
    Base class for multiple selectors for classes that allow exactly one choice.
    Such fields are naturally required by default, since there is always at
    least one choice that must be selected.
    """
    types_data = (str,)
    types_parse = (type(None), unicode)
    types_render = (list,)

    def __init__( self, name, values,
                  label=None, hidden=None, initial=None, nocheck=None ):

        # Check the type of initial, which must be one of the types accepted
        # for values.
        if isinstance(initial, int):
            initial = str(initial)
        assert isinstance(initial, (type(None),) + _OneChoiceField.types_data)

        # Initialize base classes, always set as required.
        _MultipleField.__init__(self, name, values, label, hidden,
                                initial, nocheck)

    def parse_value( self, pvalue ):
        # See note about a value expected to have been submitted for the field,
        # in parse_value() docstring.

        if pvalue is None or pvalue == u'':
            # We indicate a required error: one of the radio buttons or menu
            # items should always be set. An empty value should never occur,
            # this could be indicated as an internal error.  However, if this is
            # a browser problem, it is possible that the browser has a bug that
            # it allows a radio button or menu field to not be set to at least
            # one value, in which case it is not really the user's fault, and
            # the right thing to do is to return an error to the user so that he
            # can make the desired choice.
            raise ValueError(msg_registry['one-choice-required'], None)

        if isinstance(pvalue, list):
            # We really should not be receiving more than one value here.
            raise RuntimeError(
                "Error: internal error with radio value encoding")

        # Decode the string as a ascii strings.
        try:
            dvalue = pvalue.encode('ascii')
        except UnicodeEncodeError:
            # The values really should be ascii-encodeable strings...
            raise RuntimeError(
                "Error: internal error with radio value encoding")

        # Check the given argument against the value.
        self.checkvalues( [dvalue] )

        return dvalue

    def render_value( self, dvalue ):
        # Nothing special to do, the selection string should remain that way
        # for the renderer to do its thing.
        return dvalue


#-------------------------------------------------------------------------------
#
class RadioField(_OneChoiceField, _Orientable):
    """
    Field that renders radio buttons, which allow the user to select a single
    choice among many.  This field is rendered in a specific orientation.
    """
    css_class = 'radio'

    def __init__( self, name, values,
                  label=None, hidden=None, initial=None,
                  nocheck=None, orient=_Orientable.ORI_VERTICAL ):
        _OneChoiceField.__init__(self, name, values, label, hidden,
                                 initial, nocheck)
        _Orientable.__init__(self, orient)

#-------------------------------------------------------------------------------
#
class MenuField(_OneChoiceField):
    """
    Field that renders an option menu, which allow the user to select a single
    choice among many.
    """
    css_class = 'menu'

    def __init__( self, name, values, label=None, hidden=None,
                  initial=None, nocheck=None ):
        _OneChoiceField.__init__(self, name, values, label, hidden,
                                 initial, nocheck)


#-------------------------------------------------------------------------------
#
class _ManyChoicesField(_MultipleField):
    """
    Zero or many checkbox choices among many.
    """
    types_data = (type(None), str, list)
    types_parse = (type(None), unicode, list)
    types_render = (list,)

    def __init__( self, name, values, label=None, hidden=None,
                  initial=None, nocheck=None ):

        # Check the type of initial, which must be one of the types accepted for
        # values.
        if isinstance(initial, int):
            initial = str(initial)
        elif isinstance(initial, (list, tuple)):
            newinitial = []
            for el in initial:
                if isinstance(el, int):
                    el = str(int)
                else:
                    assert isinstance(el, str)
                newinitial.append(el)
            initial = newinitial
        assert isinstance(initial, (type(None),) + _ManyChoicesField.types_data)

        # Initialize base classes, always set as required.
        _MultipleField.__init__(self, name, values, label, hidden,
                                initial, nocheck)

    def parse_value( self, pvalue ):
        if pvalue is None or pvalue == u'':
            # Nothing was selected, so we simply return an empty list.
            return []
        elif isinstance(pvalue, unicode):
            # Make it a list of one element, and then we process the list below.
            pvalue = [pvalue]

        # At this point we're really expecting a list type.
        assert isinstance(pvalue, list)
        dvalue = []
        for val in pvalue:
            # Decode the string as an ascii string and append to result.
            try:
                decval = val.encode('ascii')
                dvalue.append(decval)
            except UnicodeEncodeError:
                # The values really should be ascii-encodeable strings...
                raise RuntimeError(
                    "Error: internal error with radio value encoding")

        # Check the given argument against the value.
        self.checkvalues(dvalue)

        return dvalue

    def render_value( self, dvalue ):
        # Nothing special to do, the selection string should remain that way
        # for the renderer to do its thing.
        return dvalue


#-------------------------------------------------------------------------------
#
class CheckboxesField(_ManyChoicesField, _Orientable):
    """
    Zero, one or many checkbox choices.  This field defines a row or column of
    checkboxes.
    """
    css_class = 'checkboxes'

    def __init__( self, name, values,
                  label=None, hidden=None, initial=None,
                  nocheck=None, orient=_Orientable.ORI_VERTICAL ):

        _ManyChoicesField.__init__(self, name, values, label, hidden,
                                   initial, nocheck)
        _Orientable.__init__(self, orient)

#-------------------------------------------------------------------------------
#
class ListboxField(_ManyChoicesField, _OneChoiceField, _OptRequired):
    """
    A listbox higher than one entry.  Either ''zero or one'' choices, OR ''zero
      or many'' choices can be made, thus, a listbox can be in one of two modes:

    - SINGLE mode: it allows zero or one choices;
    - MULTIPLE mode: it allows zero, one or many choices;

    If you want to provide a single mode where the listbox forces the user to
    provide at least one value, use the 'required' option.

    """
    types_data = _ManyChoicesField.types_data
    types_parse = _ManyChoicesField.types_parse
    types_render = _ManyChoicesField.types_render

    css_class = 'listbox'

    __default_size = 5

    def __init__( self, name, values, label=None, hidden=None, initial=None,
                  required=None, nocheck=None, multiple=False, size=None ):
        """
        :Arguments:

        - 'required' -> bool: whether the listbox forces a minimum of one choice
          to be made;

        - 'nocheck' -> bool: (See class _MultipleField for details.)

        - 'multiple' -> bool: set this to True if the field should allow more
          than one value maximum to be set.

        - 'size' -> int: the height/number of visible elements of the listbox.
          By default, if left unset, it will use a reasonable minimum or the
          number of values if very small.

        """
        assert isinstance(multiple, (bool, int))
        self.multiple = multiple
        "Whether the listbox allows more than a maximum of one choice."

        if multiple:
            _ManyChoicesField.__init__(self, name, values, label, hidden,
                                       initial, nocheck)
        else:
            _OneChoiceField.__init__(self, name, values, label, hidden,
                                     initial, nocheck)
        _OptRequired.__init__(self, required)

        self.size = size
        "The number of visible elements that the render should set."

        # Set a more sensible default if it was not set.
        if size is None:
            if values:
                self.size = min(len(values), self.__default_size)
            else:
                self.size = self.__default_size

    def parse_value( self, pvalue ):
        # Check the required value, this forces at least one choice to be
        # present.
        pvalue = _OptRequired.parse_value(self, pvalue)

        # Otherwise, parse with whichever method is appropriate.
        if self.multiple:
            return _ManyChoicesField.parse_value(self, pvalue)
        else:
            return _OneChoiceField.parse_value(self, pvalue)



#-------------------------------------------------------------------------------
#
class JSDateField(Field): # Is always required.
    """
    A fancy Javascript-based date field.

    This is an adaptation for this form handling library of a nice
    Javascript-based date input field found at http://www.jasonmoon.net/.  The
    conditions of utilisation of that code is that a notice should be present
    and kept intact somewhere in the comments.
    """
    types_data = (type(None), datetime.date,)
    types_parse = (type(None), unicode,)
    types_render = (unicode,)
    css_class = 'jsdate'

    # Public data used for adding the script reference to the head.
    script = 'calendarDateInput.js'
    script_notice = """
    Jason's Date Input Calendar- By Jason Moon http://www.jasonmoon.net/
    Script featured on and available at http://www.dynamicdrive.com
    Keep this notice intact for use.
    """

    __date_re = re.compile('(\d\d\d\d)(\d\d)(\d\d)')

    __script_re = '^[a-zA-Z_]+$'

    def __init__( self, name, label=None, hidden=None, initial=None ):
        """
        Note: there is a special constraint on the varname of the field due to
        the Javascript code involved (see below).
        """
        Field.__init__(self, name, label, hidden, initial)

        # This verification is required for the JS calendar.
        assert re.match(JSDateField.__script_re, name)

    def parse_value( self, pvalue ):
        # See note about a value expected to have been submitted for the field,
        # in parse_value() docstring.
        assert pvalue is not None

        # Encode value into ascii.
        try:
            dvalue = pvalue.encode('ascii')
        except UnicodeEncodeError:
            # This should not happen if the value comes from the code.
            raise RuntimeError(
                "Error: internal error with input from JSDateField.")

        # Match the given string, it should always match.
        mo = JSDateField.__date_re.match(dvalue)
        assert mo

        # Convert into date.
        try:
            dvalue = datetime.date(*map(int, mo.groups()))
        except ValueError, e:
            raise ValueError(msg_registry['date-invalid'] % dvalue, None)

        return dvalue

    def render_value( self, dvalue ):
        # Convert the date object in a format suitable for being accepted by the
        # Javascript code.
        rvalue = dvalue.strftime('%Y%m%d')
        return rvalue


#-------------------------------------------------------------------------------
#
class FileUploadField(Field, _OptRequired):
    """
    A file being sent by the client.  The returned value is an instance of the
    FileUpload class.

    There are lots of details about file upload mechanics at
    http://www.cs.tut.fi/~jkorpela/forms/file.html

    Note: depending on the web framework using this, it might be possible to get
    access to the filename, to set it for as the replacement value.  Check, this
    is possible
    """

    types_data = (type(None), types.InstanceType,)
    types_parse = (type(None), types.InstanceType, str,)
    types_render = (unicode,)
    css_class = 'file'

    def __init__( self, name, label=None, hidden=None,
                  initial=None, required=None,
                  filtpattern=None ):
        Field.__init__(self, name, label, hidden, initial)
        _OptRequired.__init__(self, required)

        self.filtpattern = filtpattern
        """Filter string to initialize the browser dialog on the client-side
        with. This corresponds to the 'accept' attribute of the corresponding
        HTML input field."""

    def parse_value( self, pvalue ):
        """
        Check the type of the object that is given to us.  Depending on the
        framework which is using this library, the nature of the object can
        vary, and we support various things here, and this could be extended.
        If you have some type of object that is generic enough or part of a
        widely popular framework, please contact the author for inclusion.

        Note: The replacement value for file uploads is not supported in many
        browser (e.g. see
        http://www.cs.tut.fi/~jkorpela/forms/file.html#value), but is
        supported by certain browsers.  Thus we will try to set the
        replacement value to the value of the filename, if the filename is
        available.  Otherwise, no biggie, the field's filename will be lost.

        We expect that we will not build complex forms that include a file
        upload field, and so this should not be a big problem in practice.

        Note(2): we avoid code dependencies on the given objects by checking for
        their types 'by name'.
        """

        # Check for strings.
        if isinstance(pvalue, str):
            # We got data as a string, wrap around file-like object.
            #
            # Note: we need to accept string types, since from the mechanize
            # library submit, that allows us to write tests, that's what we seem
            # to get.
            dvalue = StringIO(arg)

        elif isinstance(pvalue, types.InstanceType):
            # Check for a mod_python Field class.
            if pvalue.__class__.__name__ == 'Field':
                # We wrap it in a FileUpload object from this module.
                pvalue = FileUpload(pvalue)

            # Here check if it's a FileUpload object that we just created above
            # from a Field or a FileUpload object from the draco library that
            # did the same.  The draco class is functionally the same as the one
            # we provide.
            if pvalue.__class__.__name__ == 'FileUpload':
                # We need to check if the file is empty, because we still might
                # get a file object if the user has not submitted anything (this
                # may be a bug in draco or mod_python).
                pvalue.file.seek(0, 2)
                size = arg.file.tell()
                if size > 0:
                    # Success, rewind and use.
                    pvalue.file.seek(0)
                    dvalue = pvalue
                else:
                    # The file is empty, mark as such.
                    dvalue = None
            else:
                # Check for anything that has a read() method.
                if hasattr(pvalue, 'read'):
                    dvalue = pvalue
        else:
            # Otherwise it's not an instance nor a string, we really don't know
            # what to do.
            raise RuntimeError(
                "Internal error: type for file parsing unknown.")

        # Check the required value, this forces at least one choice to be
        # present. We don't delegate to the base class on purpose, this is a
        # special case.
        if self.required and pvalue is None:
            # We indicate an error mentioning that this field was required.
            raise ValueError(msg_registry['error-required-value'], None)

        return dvalue

    def render_value( self, dvalue ):
        # Never render anything in there, it's not really used by browsers
        # anyway (at least not without a warning, when it is, e.g. Opera).
        return None


class FileUpload:
    """
    Adapter class for the mod_python Field class that implements the file
    interface.  This slightly changes the semantics of mod_python's Field
    class. It imports the file operations from the temporary file to the current
    class so it can be used as a file.
    """

    def __init__( self, field ):
        self.field = field

    def __getattr__( self, name ):
        """
        Aggregate file methods into the current object.
        """
        if hasattr(self.field.file, name):
            attr = getattr(self.field.file, name)
            if callable(attr):
                return attr
        return getattr(self.field, name)

