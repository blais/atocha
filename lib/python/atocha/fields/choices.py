#!/usr/bin/env python
#
# $Id$
#

"""
Fields ...
"""

# stdlib imports
import re
from types import NoneType

# atocha imports.
from atocha.field import Field, FieldError
from atocha.field import OptRequired, Orientable, ORI_VERTICAL
from atocha.messages import msg_registry, msg_type


__all__ = ['RadioField', 'MenuField', 'CheckboxesField', 'ListboxField',]


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
    used internally only, and not as user-visible strings).  However, if the
    values are integers, they will be automatically converted to strings, so
    that values are always strings.

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
    types_parse = (NoneType, list,)
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
        self.valueset = {}
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
                self.valueset[value] = label


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
class _OneChoiceField(_MultipleField):
    """
    Base class for multiple selectors for classes that allow exactly one choice.
    Such fields are naturally required by default, since there is always at
    least one choice that must be selected.
    """
    types_data = (str,)
    types_parse = (NoneType, unicode, list)
    types_render = (str,)

    def __init__( self, name, values,
                  label=None, hidden=None, initial=None, nocheck=None ):

        # Check the type of initial, which must be one of the types accepted
        # for values.
        if isinstance(initial, int):
            initial = str(initial)
        assert isinstance(initial, (NoneType,) + _OneChoiceField.types_data)

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
            raise FieldError(msg_registry['one-choice-required'])

        if isinstance(pvalue, list):
            # We really should not be receiving more than one value here.
            raise RuntimeError(
                "Error: internal error with radio (list received).")

        # Decode the string as a ascii strings.
        try:
            dvalue = pvalue.encode('ascii')
        except UnicodeEncodeError:
            # The values really should be ascii-encodeable strings...
            raise RuntimeError(
                "Error: internal error with radio (value encoding)")

        # Check the given argument against the value.
        self.checkvalues( (dvalue,) )

        return dvalue

    def render_value( self, dvalue ):
        if dvalue is None:
            if self.values:
                return self.values[0][0]
            else:
                # Not sure what to do if there are not field values.
                raise RuntimeError("Error: single selection field without "
                                   "values... cannot set default state.")

        # Nothing special to do, the selection string should remain that way
        # for the renderer to do its thing.
        return dvalue

    def display_value( self, dvalue ):
        # Translate the label of the value before returning it.
        return _(self.valueset[dvalue])


#-------------------------------------------------------------------------------
#
class RadioField(_OneChoiceField, Orientable):
    """
    Field that renders radio buttons, which allow the user to select a single
    choice among many.  This field is rendered in a specific orientation.
    """
    css_class = 'radio'

    def __init__( self, name, values,
                  label=None, hidden=None, initial=None,
                  nocheck=None, orient=ORI_VERTICAL ):
        _OneChoiceField.__init__(self, name, values, label, hidden,
                                 initial, nocheck)
        Orientable.__init__(self, orient)

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
    types_data = (list,)
    types_parse = (NoneType, unicode, list)
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
        assert isinstance(initial, (NoneType,) + _ManyChoicesField.types_data)

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
        if dvalue is None:
            return []

        # Nothing special to do, the selection string should remain that way
        # for the renderer to do its thing.
        return dvalue

    def display_value( self, dvalue ):
        # Get labels and join them.
        # Note: Translate the labels of the value before returning it.
        labels = [_(self.valueset[x]) for x in dvalue]
        return u', '.join(labels)


#-------------------------------------------------------------------------------
#
class CheckboxesField(_ManyChoicesField, Orientable):
    """
    Zero, one or many checkbox choices.  This field defines a row or column of
    checkboxes.
    """
    css_class = 'checkboxes'

    def __init__( self, name, values,
                  label=None, hidden=None, initial=None,
                  nocheck=None, orient=ORI_VERTICAL ):

        _ManyChoicesField.__init__(self, name, values, label, hidden,
                                   initial, nocheck)
        Orientable.__init__(self, orient)

#-------------------------------------------------------------------------------
#
class ListboxField(_ManyChoicesField, _OneChoiceField, OptRequired):
    """
    A listbox higher than one entry.  Either ''zero or one'' choices, OR ''zero
      or many'' choices can be made, thus, a listbox can be in one of two modes:

    - SINGLE mode: it allows zero or one choices, returns a str or None;
    - MULTIPLE mode: it allows zero, one or many choices, returns a list;

    If you want to provide a single mode where the listbox forces the user to
    provide at least one value, use the 'required' option.

    """
    # Must include all possibilities for many or one: list for many choices, str
    # for a single choice, None for zero choice.
    types_data = (list, str, NoneType,)
    types_parse = _ManyChoicesField.types_parse + _OneChoiceField.types_parse
    types_render = _ManyChoicesField.types_render + _OneChoiceField.types_render

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
        OptRequired.__init__(self, required)

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
        pvalue = OptRequired.parse_value(self, pvalue)

        # Otherwise, parse with whichever method is appropriate.
        if self.multiple:
            return _ManyChoicesField.parse_value(self, pvalue)
        else:
            # Deal with the case where no value is selected. This is legal for a
            # 'single' Listbox (and is what makes it unique and useful over a
            # menu with an extra 'no-choice' item).
            if pvalue is None:
                return None
            return _OneChoiceField.parse_value(self, pvalue)

    def display_value( self, dvalue ):
        if self.multiple:
            return _ManyChoicesField.display_value(self, dvalue)
        else:
            # Deal with the case where no value is selected. See comment above.
            if dvalue is None:
                return u''
            return _OneChoiceField.display_value(self, dvalue)
