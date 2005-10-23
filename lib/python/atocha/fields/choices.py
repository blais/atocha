#!/usr/bin/env python
#
# $Id$
#

"""
Single or Multiple Choice Fields
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

    The choices are ascii str's only, they cannot be unicode (this is a
    limitation we impose ourselves, as a recognition that the choices are to be
    used internally only, and not as user-visible strings).  However, if the
    choices are integers, they will be automatically converted to strings, so
    that choices are always strings.

    One issue with the choices fields is that the set of valid choices may be
    generated dynamically, and therefore sometimes we need to be able to create
    the field at a moment where we do not know in advance what the choices will
    be.  If this is the case:

    - for rendering: we set the choices on the field right before rendering it.

    - for parsing: the field has an option to avoid checking against choices set
      on it.  You can set that field and then do some manual checking using the
      protocol provided by the form parser.

    See the concrete fields for an explanation of the kinds of parsing input
    that they can accept, and how they deal with them.
    """
    types_parse = (NoneType, list,)
    types_render = (list,)

    attributes_mandatory = (
        ('choices', 'Sequence of str or (str, unicode)',
         """Choice-label pairs: the ordered choices, to be rendered and checked
        against when parsing.  This is not a mapping because order is important
        for rendering.  If the elements of the list are pairs, the label is used
        for the user-visible strings to be used when rendering the widget.  Note
        that we also accept integers for choices instead of ascii strings, but
        these will be automatically converted to strings."""),
        )
        
    attributes_declare = (
        ('nocheck', 'bool',
         """Set this to True if you want to prevent the parser from
         cross-checking the values against the choices set in the instance of
         this field.  When parsing, do not perform checks specific to the
         choices set on against the received values. This is useful if the set
         of choices for this field is generated dynamically and you will do your
         validation by hand.  Another thing that can be done is to not use this
         but to call setchoice() before running the parser on the arguments, if
         in the handler you know which choices are possibly valid and would like
         to use the parsing code provided in this field."""),
        )

    def __init__( self, name, choices, label, attribs ):

        self.nocheck = attribs.pop('nocheck', None)

        Field.__init__(self, name, label, attribs)


        self.choices = None
        "(Internal use only.) List of the possible choices for this field"

        self.choiceset = None
        """(Internal use only.) Set of the possible choices for this field,
        maintainde for fast lookup only."""

        # Set the initial choices for this field.
        self.setchoices(choices)


    def setchoices( self, choices ):
        """
        Set the choices that this field renders and parses.  'choices' is of the
        same types as described in the attributes.
        """
        self.choiceset = {}
        self.choices = []

        # Accumulator for the normalized choices.
        normchoices = []

        if choices is None:
            return
        else:
            assert isinstance(choices, (list, tuple))

            # Normalize all the choices into pairs.
            for el in choices:

                choice = label = None

                # Accept simple choices.
                if isinstance(el, (int, str)):
                    choice = el

                # And of course, a choice-label pair.
                elif isinstance(el, tuple):
                    assert len(el) == 2
                    choice, label = el

                else:
                    raise RuntimeError(
                        "Error: wrong type of choice in initializer element: %s."
                        % type(el))

                # Convert integer choice into string if necessary.
                if isinstance(choice, int):
                    choice = str(choice)

                # If the label is not set, it takes the same choice as the label
                # (convert to unicode from ascii).
                if label is None:
                    label = choice.decode('ascii')
                else:
                    # Other we check to make sure that the label is of type
                    # msg_type, which is the required type for all the
                    # user-visible choices.
                    assert isinstance(label, msg_type)

                # Just more zealous sanity checking.
                assert isinstance(choice, str)

                # We add the new pair to our internal, normalized set of
                # choices.
                self.choices.append( (choice, label) )
                self.choiceset[choice] = label


    def checkvalues( self, values ):
        """
        Cross-check values agains the set of possible choices for this field.
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

            if value not in self.choiceset:
                # Note: this could be an internal error.
                raise RuntimeError("Error: internal error checking values "
                                   "against choices in a multiple field.")

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

    def __init__( self, name, choices, label, attribs ):

        # Check the type of initial, which must be one of the types accepted
        # for choices.
        if 'initial' in attribs:
            initial = attribs['initial']
            if isinstance(initial, int):
                initial = str(initial)
            assert isinstance(initial, (NoneType,) + _OneChoiceField.types_data)
            attribs['initial'] = initial
                
        # Initialize base classes, always set as required.
        _MultipleField.__init__(self, name, choices, label, attribs)


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
            if self.choices:
                return self.choices[0][0]
            else:
                # Not sure what to do if there are not field values.
                raise RuntimeError("Error: single selection field without "
                                   "values... cannot set default state.")

        # Nothing special to do, the selection string should remain that way
        # for the renderer to do its thing.
        return dvalue

    def display_value( self, dvalue ):
        # Translate the label of the value before returning it.
        return _(self.choiceset[dvalue])


#-------------------------------------------------------------------------------
#
class RadioField(_OneChoiceField, Orientable):
    """
    Field that renders radio buttons, which allow the user to select a single
    choice among many.  This field is rendered in a specific orientation.
    """
    css_class = 'radio'

    def __init__( self, name, choices, label=None, **attribs ):
        RadioField.validate_attributes(attribs)

        Orientable.__init__(self, attribs)
        _OneChoiceField.__init__(self, name, choices, label, attribs)

#-------------------------------------------------------------------------------
#
class MenuField(_OneChoiceField):
    """
    Field that renders an option menu, which allow the user to select a single
    choice among many.
    """
    css_class = 'menu'

    def __init__( self, name, choices, label=None, **attribs ):
        MenuField.validate_attributes(attribs)

        _OneChoiceField.__init__(self, name, choices, label, attribs)


#-------------------------------------------------------------------------------
#
class _ManyChoicesField(_MultipleField):
    """
    Zero or many checkbox choices among many.
    """
    types_data = (list,)
    types_parse = (NoneType, unicode, list)
    types_render = (list,)

    def __init__( self, name, choices, label, attribs ):

        # Check the type of initial, which must be one of the types accepted for
        # choices.
        if 'initial' in attribs:
            initial = attribs['initial']
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
            attribs['initial'] = initial

        # Initialize base classes, always set as required.
        _MultipleField.__init__(self, name, choices, label, attribs)


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
        labels = [_(self.choiceset[x]) for x in dvalue]
        return u', '.join(labels)


#-------------------------------------------------------------------------------
#
class CheckboxesField(_ManyChoicesField, Orientable):
    """
    Zero, one or many checkbox choices.  This field defines a row or column of
    checkboxes.
    """
    css_class = 'checkboxes'

    def __init__( self, name, choices, label=None, **attribs ):
        CheckboxesField.validate_attributes(attribs)

        Orientable.__init__(self, attribs)
        _ManyChoicesField.__init__(self, name, choices, label, attribs)

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

    attributes_declare = (
        ('multiple', 'bool',
         """Set this to True if the field should allow more than one value
         maximum to be set."""),

        ('size', 'int',
         """The height/number of visible elements of the listbox.  By default,
         if left unset, it will use a reasonable minimum or the number of
         choices if very small."""),
        )

    __default_size = 5

    def __init__( self, name, choices, label=None, **attribs ):
        ListboxField.validate_attributes(attribs)

        self.multiple = attribs.pop('multiple', False)
        assert isinstance(self.multiple, (bool, int))
        
        # Set a more sensible default if it was not set.
        self.size = attribs.pop('size', None)
        if self.size is None:
            if choices:
                self.size = min(len(choices), self.__default_size)
            else:
                self.size = self.__default_size

        OptRequired.__init__(self, attribs)
        if self.multiple:
            _ManyChoicesField.__init__(self, name, choices, label, attribs)
        else:
            _OneChoiceField.__init__(self, name, choices, label, attribs)


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

