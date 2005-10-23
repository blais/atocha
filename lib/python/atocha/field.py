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
import sys
if sys.version_info[:2] < (2, 4):
    from sets import Set as set

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

    Attributes
    ----------

    Every field class should define the following class attributes:

    - 'attributes_mandatory' -> sequence of (name, typedesc, description)
      pairs. This states that the current class requires the given list of
      parameters.

    - 'attributes_declare' -> sequence of (name, typedesc, description)
      pairs. This states that the current class supports the given list of
      attributes.

    - 'attributes_delete' -> sequence of attribute names. This states the the
      given class removes the given attributes from the list of valid attributes
      that it supports.

    Note that the computation of the final list of attributes is done lazily,
    and that you do not need to append those classes attributes to those of the
    parent, in the derived classes. The aggregation of attributes from the base
    classes is made automatically.

    These declarations are used to verify validity of given attributes at
    runtime, and to generate documentation of the fields.

    Types
    -----

    Every field class must define the following class attributes:

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

    # State definition enums.
    _states = NORMAL, READONLY, DISABLED, HIDDEN = range(1, 5)
    
    #---------------------------------------------------------------------------
    #

    # Attributes declarations.
    attributes_mandatory = (
        ('name', 'str',
        """Unique identifier name for the field, and name of the form
        variables as well."""),
        )

    attributes_declare = (
        ('label', 'str', "The visible label used by the form rendering."),

        # We would like to keep the varnames feature a bit hidden for now, to be
        # used by subclasses and not abused by creators of forms unless really
        # needed.
        #
        # ('varnames', 'tuple of str', """Tuple of variable names used for the
        # field, by default, a one-element tuple, of the same name as the field
        # itself."""),

        ('state', 'one of Field._states',
        """Whether the field is to be rendered visible, readonly,
        disabled or hidden.  This value represents the default state, and can be
        overridden when the field is rendered. You can use the values
        Field.NORMAL (default), Field.READONLY, Field.DISABLED, Field.HIDDEN.
        """),

        ('initial', 'valid data type for Field',"""Default value that is used for
        rendering the field with known initial conditions if no value is given
        for it.  Important note:  this value is not used by the parsing at all.
        If an argument is missing during parsing, the value associated with the
        field will be set to None. This is NOT a default value to be provided by
        the parser if the field is not submitted. """),
        )

    attributes_delete = ()

    
    def get_attributes( cls ):
        """
        Lazily compute the field attributes and returns a set of valid
        attributes and a list of (name, typedesc, desc) tuples.
        """
        if '_attributes' not in cls.__dict__:

            # Build the list of classes in order of inheritance.
            allclasses, clsstack = [], [cls]
            while clsstack:
                thiscls = clsstack.pop()
                allclasses.append(thiscls)
                clsstack.extend(thiscls.__bases__)
            allclasses.reverse()

            # Accumulate the tuples of attributes, in order.
            mattmap, mattorder = {}, []
            attmap, attorder = {}, []
            for thiscls in allclasses:
                if 'attributes_mandatory' in thiscls.__dict__:
                    for a in thiscls.__dict__['attributes_mandatory']:
                        attmap[ a[0] ] = a + (True,)
                        mattorder.append( a[0] )

                if 'attributes_declare' in thiscls.__dict__:
                    for a in thiscls.__dict__['attributes_declare']:
                        attmap[ a[0] ] = a + (False,)
                        attorder.append( a[0] )

                if 'attributes_delete' in thiscls.__dict__:
                    for aname in thiscls.__dict__['attributes_delete']:
                        del attmap[aname]

            # Compute the final list of attributes and their description.
            adescs, aset = [], set()
            for aname in mattorder + attorder:
                try:
                    a = attmap[aname]
                    assert len(a) == 4
                    adescs.append(a)
                    aset.add(aname)
                except KeyError:
                    pass

            cls._attributes_set = aset
            cls._attributes = adescs
            
        return cls._attributes_set, cls._attributes

    get_attributes = classmethod(get_attributes)
    
    def validate_attributes( cls, attribs ):
        """
        Validates that all the attributes names given are supported.
        """
        if not __debug__:
            return # Only in optimized mode.
        
        aset, adescs = cls.get_attributes()
        errors = []
        for aname in attribs.iterkeys():
            if aname not in aset:
                errors.append(aname)
        if errors:
            raise RuntimeError(
                "Error: attributes '%s' not supported in field class '%s'." %
                (', '.join(errors), cls.__name__))

    validate_attributes = classmethod(validate_attributes)

    #---------------------------------------------------------------------------
    #
    def __init__( self, name, label, attribs ):
        assert isinstance(name, str)
        assert isinstance(label, (NoneType, msg_type))

        self.name = name
        
        self.label = label

        self.varnames = attribs.pop('varnames', [name])
        for varname in self.varnames:
            assert Field.varname_re.match(varname)

        self.state = attribs.pop('state', Field.NORMAL)
        assert self.state is None or self.state in Field._states

        # Make sure that the initial value is of an acceptable type for this
        # field.
        self.initial = attribs.pop('initial', None)
        assert isinstance(self.initial, (NoneType,) + self.types_data)

        # Check that all attributes have been popped.
        if attribs:
            raise RuntimeError(
                "Error: unsupported attributes '%s' in field '%s'." %
                (', '.join(attribs.keys()), self.name))

    def __str__( self ):
        """
        Returns a human-readable version of the field.
        """
        return "<Field name=%s>" % self.name

    def ishidden( self ):
        """
        Returns true if this field is hidden.
        """
        return self.state == Field.HIDDEN

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
    Base class for all fields which can be OPTIONALLY REQUIRED, that is, which
    can take the 'required' option which allows them to check whether the input
    was submitted or not.

    The required field is checked via the parse_value() method for each field
    type, and not in the parser itself (previous versions of this library used
    to do that).

    Important note: the 'required' option does not make sense for all the field
    types, due to the nature of the submission protocol (for example, for the
    checkboxes, the absence of the field value means a value of False, so we
    cannot really check if the value was False or ''not submitted''.  This is
    why some of the fields do not support the required field.
    """

    attributes_declare = (
        ('required', 'bool',
        """Indicates that if the value is missing from the arguments during
        parsing, and error will be signaled for that input.  If 'required' is
        not set, a missing argument will produce a value of None in the parser
        for the corresponding field."""),
        )

    def __init__( self, attribs ):
        self.required = bool(attribs.pop('required', False))
        assert isinstance(self.required, bool)

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

    attributes_declare = (
        ('orient', 'One of ORI_VERTICAL, ORI_HORIZONTAL',
        """Orientation of the mini-table for layout of multiple inputs."""),
        )

    def __init__( self, attribs ):

        self.orient = attribs.pop('orient', ORI_VERTICAL)
        assert self.orient in [ORI_HORIZONTAL, ORI_VERTICAL]
        """Orientation of the field for rendering."""


