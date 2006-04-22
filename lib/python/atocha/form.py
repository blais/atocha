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
Form definition and exceptions.
"""


# stdlib imports
import sys
if sys.version_info[:2] < (2, 4):
    from sets import Set as set
import re
from types import NoneType

# atocha imports
from atocha import AtochaError, AtochaInternalError
from field import Field, FieldError
from fields.uploads import FileUploadField, FileUpload
from messages import msg_registry, msg_type


__all__ = ['Form']


_python_keywords = set(
    ('and', 'del', 'for', 'is', 'raise', 'assert', 'elif', 'from', 'lambda',
    'return', 'break', 'else', 'global', 'not', 'try', 'class', 'except', 'if',
    'or', 'while', 'continue', 'exec', 'import', 'pass', 'yield', 'def',
    'finally', 'in', 'print',))


#-------------------------------------------------------------------------------
#
class Form:
    """
    A form is essentially a container for a number of input fields with some
    special attributes.

    The input fields are converted to the output variables by the parsing code,
    and the form definition can be used by renderers to produce HTML output for
    the HTML forms.

    Each form must have a name.  Optional fields can be specified as keyword
    arguments (that otherwise have reasonable default values), are:

    - 'submit': submit button name, which can also be a tuple of (value, label)
      pairs for each submit button to be rendered, to indicate multiple submit
      buttons.;

    - 'action': the action type, usually a URL for the handler for this form,
      but this can be any data type, so that we can implement delayed evaluation
      of the action target in a given renderer;

    - 'method': the submit method (GET or POST);

    - 'encoding': the encoding that the form will accept to receive.

    Forms can be rendered by specifying an appropriate renderer class.  Note
    that the optional values may be specified later as well, at the time of
    rendering the form, if the renderer class supports it.
    """

    __def_action = None
    __def_method = 'POST'
    __def_enctype = None # 'application/x-www-form-urlencoded'
    __def_enctype_file = 'multipart/form-data'
    __def_accept_charset = 'UTF-8'

    def __init__( self, name, *fields, **kwds ):
        """
        Form creation.  You can specify 'action', 'submit' (button name) and
        'method' (GET or POST) here.
        """
        assert name and isinstance(name, str)
        self.name = name
        "The name of the form, which appears in the HTML rendering as well."

        # assert isinstance(action, str) # Accept any data type to support
                                         # delayed evaluation.
        self.action = kwds.get('action', self.__def_action)
        """The action of the form. This is the URL which will handle the form
        submit."""

        self.submit = kwds.get('submit', None)
        """The string on the submit button, or a tuple of strings if there are
        many."""
        if self.submit is None:
            self.submit = msg_registry.get_notrans('submit-button')

        # Check the types.
        if isinstance(self.submit, (list, tuple)):
            for n in self.submit:
                if isinstance(n, tuple):
                    assert isinstance(n[1], msg_type)
                else:
                    raise AtochaInternalError(
                        "Internal error with submit types.")
        else:
            assert isinstance(self.submit, msg_type)
        assert self.submit

        self.method = kwds.get('method', None)
        if self.method is None:
            self.method = self.__def_method
        assert self.method in ('GET', 'POST')
        "The submit method, GET or POST."

        self.enctype = kwds.get('enctype', self.__def_enctype)
        """Encapsulation type for the form data.  This should be set
        appropriately, depending on the presence of a file upload input."""

        self.accept_charset = kwds.get('accept_charset',
                                       self.__def_accept_charset)
        "The charset encoding that the form handler will accept."

        reset = kwds.get('reset', None)
        if reset and isinstance(reset, (bool, int)):
            reset = msg_registry.get_notrans('reset-button')
        assert isinstance(reset, (NoneType, msg_type))
        self.reset = reset
        """Whether a reset button should be provided. The value can be either a
        string to be translated later or a bool/int, where we will use the
        default value."""
            
        self._fields = []
        "The list of fields, essentially to keep the ordering."

        self._fieldsmap = {}
        "A map of all the fields."

        # Unroll nested lists of fields.
        def unroll_fields( forl ):
            if isinstance(forl, Field):
                ufields.append(forl)
            elif isinstance(forl, (list, tuple)):
                for f in forl:
                    unroll_fields(f)
            else:
                assert False

        ufields = []
        unroll_fields(fields)

        for field in ufields:
            assert isinstance(field, Field)
            self.addfield(field)

        # Check that the submit button values, if there are many, do not overlap
        # with the fields variable names, otherwise the form submit will not be
        # able to do its thing reliably due to collisions in the names.
        for val in self.__get_submit_values():
            assert val not in self._fieldsmap

    def __getitem__( self, name ):
        """
        Get a field by name.  This allows you to lookup a field from the form
        directly.
        """
        return self._fieldsmap[name]

    def fields( self ):
        """
        Return a list containing the form fields.
        """
        return self._fields

    def names( self ):
        """
        Returns a list of the field names.
        """
        return [x.name for x in self._fields]

    def varnames( self ):
        """
        Returns a list of the variable names that the fields encompass.
        This will normally be the same as the field names.
        """
        varnames = []
        for fi in self._fields:
            varnames.extend(fi.varnames)
        return varnames

    def labels( self, *fieldnames ):
        """
        Returns a list of the labels of the fields.
        """
        if fieldnames is not None:
            fields = [self._fieldsmap[x] for x in fieldnames]
        else:
            fields = self._fields
        return [x.label for x in fields]

    def fetchnames( self, obj, exceptions=[], default=None ):
        """
        Fetches attributes corresponding to the form field names from the given
        object 'obj' and returns a mapping with those values.  This can be
        useful if 'obj' is an object with the values that we want to fetch to
        initialize a map before rendering a form.  'default' is used to set a
        value for fields that have a value of None.

        Note: this does not use the field variable names, but rather the actual
        field names (in fact, this is one of the places where having a different
        name for the field and its associated variable may come in handy).
        """
        values = {}
        for field in self._fields:
            if field.name in exceptions:
                continue
            try:
                v = values[field.name] = getattr(obj, field.name)
                if v is None and default is not None:
                    values[field.name] = default
            except AttributeError:
                pass
        return values

    def addfield( self, field ):
        """
        Add a field to the form. The field argument must be a Field instance.
        """
        if not isinstance(field, Field):
            raise AtochaError('Type error: Expecting a Field instance.')
        elif isinstance(field, FileUploadField):
            # If a FileUpload field is added, make sure that we modify the
            # enctype for the form appropriately.
            self.enctype = self.__def_enctype_file

        # Check against keywords.
        if field.name in _python_keywords:
            # Note: we *could* issue a warning here, but we assume that most
            # people will use the attribute syntax to access the parsed
            # arguments and it would only write something to the log file.  It's
            # really no big deal to force the user not to use field names that
            # are Python keywords.
            #
            # If you tracked this issue all the way here and are reading this
            # comment and still disagree, send email to the author and I might
            # change my mind or add a special option to allow this (because this
            # would work fine otherwise.
            raise AtochaError(
                "Error: Field name '%s' is a keyword." % field.name)

        # Check name collisions.
        if field.name in self._fieldsmap:
            raise AtochaError(
                'Error: Field name %s is already used.' % field.name)

        # Check variable name collisions.
        for fi in self._fields:
            for varname in field.varnames:
                if varname in fi.varnames:
                    raise AtochaError(
                        'Error: Collision in varnames between %s and %s.' %
                        (fi.name, field.name))
        
        self._fields.append(field)
        self._fieldsmap[field.name] = field

    def select_fields( self, only=None, ignore=None ):
        """
        Select the fields specified via 'only' and 'ignore'.
        This method implements just the only and ignore selection.

        :Arguments:

          - 'only' -> list of str: if not specified, the initial list of fields
            is the list of all fields, specified by the given field names,
            parsed in the given order.

          - 'ignore' -> list of str: specifies a list of field names to be
            ignored from this list.

        """
        # Select fields to be parsed.
        if only is None:
            fields = self._fields
        else:
            assert isinstance(only, (list, tuple))
            try:
                fields = [self._fieldsmap[x] for x in only]
            except KeyError, e:
                raise AtochaError(
                    "Error: field not present in form: %s" % str(e))

        # Remove fields to be ignored.
        if ignore is not None:
            assert isinstance(ignore, (list, tuple))

            # Note: we're making sure that all the fields specified to be
            # ignored are actually found in the list of fields, by tracking them
            # with a dict.
            ignmap = dict( [(x, None) for x in ignore] )
            newfields = []
            for fi in fields:
                if fi.name in ignmap:
                    del ignmap[fi.name]
                else:
                    newfields.append(fi)
            # We make sure that all ignored fields were selected in the first
            # place, i.e. ignmap should be empty now.
            assert not ignmap
            fields = newfields

        return fields


    def parse_field( self, fi, args ):
        """
        Parse and validate the incoming arguments for a single field.  The value
        of the parsed argument is returned, along with accompanying errors, if
        any.

        This form parsing code extracts ONLY the fields of args for which there
        are corresponding fields.  It uses the variable names specified on the
        fields for finding the values to be parsed.

        If there are errors, the replacement values are provided as per the
        protocol for the specific fields (see Field.parse_value() for full
        details of this protocol).

        Note that this method is not really meant to be called from client code;
        you should instead make use of the FormParser, which provides support
        for common patterns for parsing arguments, which include possibly some
        client code for coordinating combinations of parsed arguments and error
        rendering.

        :Arguments:

          - 'fi' -> Field instance: a field that is part of this form.

          - 'args' -> dict: a dictionary of the arguments in 'parse' types.
            This method will extract the appropriate key from the field's
            varname.

        :Return Values:

          A pair of 'success' and 'value', and there are two possibilities:

          - (0, parsed_arg): success, and the parsed argument value (which can
            be None);

          - (1, (error_message, repl_rvalue)): error, with an appropriate error
            message, unparsed replacement value (in one of the 'render' types
            for the field).  The replacement value is used to provide something
            for re-rendering a field when the value could not be parsed.

            The message is, for example, when an illegal value was supplied,
            when a field did not validate, the value was required, etc.  ...it
            depends on the field type itself.

        """
        assert isinstance(fi.varnames, list) # Sanity check.

        # Accumulate the parsed value of each of the varnames for the field.
        pvalues = {}
        for varname in fi.varnames:
            try:
                argvalue = args[varname]

                # Internal sanity check, to make sure that values of None are
                # always set by use to indicate that an argument is missing,
                # then letting the fields deal with the specific meaning of that
                # themselves.
                assert argvalue is not None

            except KeyError:
                # The argument value was not present/found...  we simply set the
                # output parsed argument to None, thus indicating that the
                # argument value was not present nor parsed.
                argvalue = None

            # Decoding.
            #
            # Decode the argument string or contained argument strings according
            # to the accept-charset specified for the form, and assuming that
            # the form has been rendered using this encoding specification.  The
            # argument can be either a str, a list or tuple or str, or a
            # FileUploadField object.
            if argvalue is None:
                # No decoding necessary for missing values.
                pvalue = None

            elif isinstance(argvalue, FileUpload):
                # Do nothing for file uploads, its encoding is separate.
                pvalue = argvalue

            elif isinstance(argvalue, str):
                # The value is a string, directly. Decode that.
                try:
                    pvalue = argvalue.decode(self.accept_charset)
                except UnicodeDecodeError, e:
                    # Broken client browser?  There is not much we can do if
                    # the browser cannot send the data in the appropriate
                    # encoding.
                    return (1, (msg_registry['error-invalid-encoding'],
                                None, None))

            elif isinstance(argvalue, list):
                # The raw argument type is a list of strings.
                # Decode each string individually to unicode before parsing.
                vallist = []
                for val in argvalue:
                    try:
                        vallist.append(val.decode(self.accept_charset))
                    except UnicodeDecodeError, e:
                        # (Same decoding error as above.)
                        return (1, (msg_registry['error-invalid-encoding'],
                                    None, None))

                pvalue = vallist

            else:
                raise AtochaInternalError(
                    'Internal error with types: unexpected type: %s.' %
                    type(argvalue))

            pvalues[varname] = pvalue

        # If there is a single pvalue, unwrap it form the list.
        if len(pvalues) == 1:
            # Use last set pvalue from the loop above.
            pass
        else:
            # Pass the dict to the field for parsing.
            pvalue = pvalues

        # Now we check that we're always giving the field an expected value
        # type for the stuff to be parsed.
        #
        # Note that we do not make an exception for the None type, which
        # indicates that the value is absent (we let the field deal with
        # that situation itself), but the field must specify itself if it
        # can accept that situation (the answer should be yes, most of the
        # time, see the types_parse in each field).
        if not isinstance(pvalue, fi.types_parse):
            raise AtochaInternalError(
                'Internal error with parse value type: %s.' % type(pvalue))

        #
        # Ask the field to parse the value itself.
        #
        try:
            parsed_dvalue = fi.parse_value(pvalue)

            # We check that the type of the parsed data value is one of the
            # expected types.
            assert isinstance(parsed_dvalue, fi.types_data)

        except FieldError, e:
            # There was an error parsing the field, i.e. the parsing raised
            # an invalid condition for that field. This is the receiving
            # part of the protocol for the fields to signal a user error.
            #
            # Pickup the error message, and the value to be set instead, if
            # given, via the second attribute of the exception (see Field
            # class for a description of the protocol).
            #
            # Note: there is always a string specified for an error.
            repl_rvalue = None
            if len(e.args) == 2:
                msg, repl_rvalue = e.args
            else:
                assert len(e.args) == 1
                msg, = e.args
            assert isinstance(msg, unicode)

            # We check that the data type of the error replacement value is
            # a valid data type for that field.
            if (repl_rvalue is not None and 
                not isinstance(repl_rvalue, fi.types_render)):
                raise AtochaInternalError(
                    ("Invalid data type of %s for field '%s', "
                     "we were expecting %s.") %
                    (repr(repl_rvalue), fi.name, repr(fi.types_render)))

            # Return error produced by the field.
            return (1, (msg, repl_rvalue))

        # Return succesfully parsed value.
        return (0, parsed_dvalue)


    def __get_submit_values( self ):
        """
        Returns a list of values for the submit buttons.
        If there is a single submit button only, returns an empty list.
        """
        # Gather the possible values for all the submit buttons.
        submit_values = []
        if not isinstance(self.submit, msg_type):
            assert isinstance(self.submit, (list, tuple))
            for n in self.submit:
                if isinstance(n, str):
                    submit_values.append(n)
                elif isinstance(n, tuple):
                    submit_values.append(n[0])
                else:
                    raise AtochaInternalError("Internal error with submit types.")
        return submit_values

    def parse_submit( self, args ):
        """
        Many submit buttons may be present in a form. If this is the case, this
        method is used to find out which of the submit buttons was pressed, and
        to validate that no two of them were submitted.  Returns the string of
        the chosen button if relevant, or None if there is a single submit
        button (and this is not relevant--this should not happen, you need not
        call this is there is a single submit button in your form).
        """
        if len(self.submit) <= 1:
            # There is a single submit button, don't bother with anything and
            # just return (Why did you call this anyway?).
            return None
        else:
            submit_values = self.__get_submit_values()

            # Find the first submit value that is present in the args.
            #
            # Note: in addition, we check that there aren't any more than a
            # single submit button values submitted at the same time, just out
            # of zealousness.
            found = None
            for sv in submit_values:
                if sv in args:
                    if found is not None:
                        raise AtochaInternalError(
                            "Error: Multiple values for submits.")
                    found = sv
                    # Note: don't break, keep checking.

            return found

    def getscripts( self ):
        """
        Returns a dict of Javascript script filenames that need to be included
        to support the widgets present in the form.
        """
        scripts = {}
        for fi in self._fields:
            for fn, notice in fi.scripts:
                if fn not in scripts:
                    scripts[fn] = notice
        return scripts

