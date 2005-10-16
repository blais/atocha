#!/usr/bin/env python
#
# $Id$
#

"""
Form fields (widgets) definitions.
"""

# stdlib imports
import re
from types import NoneType

# atocha imports.
from messages import msg_registry, msg_type


__all__ = ['Field', 'FieldError', 'ORI_HORIZONTAL', 'ORI_VERTICAL',
           'OptRequired', 'Orientable',]


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
      parsing, the value associated with the field will be set to None.  This is
      NOT a default value to be provided by the parser if the field is not
      submitted.

    Types: every field class should define the following class attributes:

    - 'types_data' -> tuple: possible data types for parsed values, which may
      include None if it is a valid data value that can be returned by the
      widget.  For values which are not required, you do NOT have to include
      None as a possibility.

    - 'types_parse' -> tuple: possible types that are given to us from the web
      application framework to parse.

    - 'types_render' -> tuple: possible types for values for prepared to be used
      for rendering.

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

    # List of JavaScript scripts (filename, notice) that may be used by a field.
    # Override this in the derived class.
    scripts = ()

    # Regular expression for valid variable names.
    varname_re = re.compile('[a-z0-9]')

    def __init__( self, name, label=None, hidden=None, initial=None ):
        assert isinstance(name, str)
        assert isinstance(label, (NoneType, msg_type))
        assert isinstance(hidden, (NoneType, bool, int))

        self.name = name
        "Name of the field."

        assert Field.varname_re.match(name)
        self.varnames = [name]
        """Tuple of variable names used for the field, by default, a one-element
        tuple, of the same name as the field itself."""
        # Note: customization for the variable names is relatively rare, so we
        # leave it to the derived classes to do the right thing.

        self.label = label
        "The visible label used by the form rendering."

        self.hidden = hidden or False
        "Whether the field is to be rendered as hidden or not."

        # Make sure that the initial value is of an acceptable type for this
        # field.
        assert isinstance(initial, (NoneType,) + self.types_data)
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
        OptRequired for more details.
        """
        try:
            isreq = getattr(self, 'required')
        except AttributeError:
            isreq = False
        return isreq

    def parse_value( self, pvalue ):
        """
        :Arguments:

        - 'pvalue': the parse value to parse, in one of the types_parse types.
          You field must be able to process all of the possible types.

        Convert the value coming from the browser into the data value.  The
        value from the browser is already decoded at the form parsing level and
        so 'pvalue' strings or strings contained within lists are actually
        already given as unicode objects.

        This method MUST return one of the valid data types or raise a
        FieldError.

        Error Protocol
        --------------

        If there is an error in parsing, due to output THAT THE USER MAY HAVE
        ENTERED, the protocol is to raise a FieldError, like this::

           raise FieldError(message, rvalue)

        The exception is initialized with an message that indicates what the
        error is, and two optional representations for the erroneous value that
        will be used to replace the entered value when re-rendering the form
        with errors (we call this the 'replacement' value): 'rvalue' (of one of
        the 'render' types) if we could not parse the data but we would sill
        like to place a replacement value in the field when re-rendering. You
        cannot specify both 'dvalue' and 'rvalue'

        Note that if there is an unexpected value or an error, which is NOT DUE
        TO USER INPUT, you should NOT raise a FieldError, but rather fail with
        an assert or a RuntimeError.  Raising FieldError is reserved for
        signaling user input error.
        """
        raise NotImplementedError # return dvalue

    def render_value( self, dvalue ):
        """
        :Arguments:

        - 'dvalue': the data value to render, in one of the types_data types, or
          can always be None as well, if the data value is not available (render
          to some fixed default).  You field must be able to process all of the
          possible types.

        Prepare the data value for rendering as part of a form rendering for an
        HTML input widget.  This is not meant for displaying the value read-only
        to the user (see special renderers to do that).  This will generally
        involve a type change, but may also implement other kinds of
        preparation.  The renderer classes are expected to know how to deal with
        the particular types to be rendered for each of the field types.

        The input value is either of one of the valid data types for the field,
        or None, to render a value that has not been set.  This method should
        always be prepared to render a dvalue of None.
        """
        raise NotImplementedError # return rvalue

    def display_value( self, dvalue ):
        """
        :Arguments:

        - 'dvalue': the data value to display, in one of the types_data types,
          or can always be None as well, if the data value is not available
          (display to some fixed default).  You field must be able to process
          all of the possible types.

        From a valid data value after having been succesfully parsed, convert
        the value from data type to unicode for user-friendly display.  This is
        meant to be used by the display renderers.

        Note that this is different from the render_value method because that is
        meant to render in a form.  We are meant to render to visible text to
        the user, such as would be displayed in a read-only table.

        Also, if you have strings that are to be translated, they should be
        translated here because the renderer will not translate them itself-- it
        is not possible, since some values can be combined, see CheckboxesField
        for example, which produces a comma-separated list of its translated
        strings for display.
        """
        raise NotImplementedError # return uvalue


#-------------------------------------------------------------------------------
#
class FieldError(Exception):
    """
    Error that is raised when user-input results in an invalid field.
    This class is used in the field parsing protocol
    (see class Field for details).
    """
    
#------------------------------------------------------------------------------
#
class OptRequired:
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
        assert isinstance(required, (NoneType, bool, int))
        self.required = required
        "Whether the argument is OPTIONALLY required or not."

    def parse_value( self, pvalue ):
        """
        Check that the field is present.  Fields which derive from this one do
        not accept None if the value is required.
        """
        if self.required and pvalue in (None, u'', '', []):
            # We indicate an error mentioning that this field was required.
            raise FieldError(msg_registry['error-required-value'])

        return pvalue


#-------------------------------------------------------------------------------
#
ORI_HORIZONTAL = 1
ORI_VERTICAL = 2

class Orientable:
    """
    Base class for fields that can be oriented.  Fields derived from this base
    class may have to be laid out horizontally or vertically.The renderers will
    most likely create a small table to lay out the radio buttons nicely, and
    this setting allows the user to choose the layout style.
    """

    def __init__( self, orient=ORI_VERTICAL ):

        assert orient in [ORI_HORIZONTAL, ORI_VERTICAL]
        self.orient = orient
        """Orientation of the field for rendering."""


