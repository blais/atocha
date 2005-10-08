#!/usr/bin/env python
#
# $Id$
#

"""
Form definition and exceptions.
"""


# stdlib imports
import types, re, datetime, StringIO

# atocha imports.
from fields import *
from messages import msg_registry, msg_type


__all__ = ['Form']


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

    - 'action': the action type, a URL for the handler for this form;

    - 'method': the submit method (GET or POST);

    - 'encoding': the encoding that the form will accept to receive.

    Forms can be rendered by specifying an appropriate renderer class.  Note
    that the optional values may be specified later as well, at the time of
    rendering the form, if the renderer class supports it.
    """

    __def_action = None
    __def_method = 'POST'
    __def_encoding = 'UTF-8'

    def __init__( self, name, *fields, **kwds ):
        """
        Form creation.  You can specify 'action', 'submit' (button name) and
        'method' (GET or POST) here.
        """
        assert isinstance(name, str)
        assert name
        self.name = name
        "The name of the form, which appears in the HTML rendering as well."

        assert isinstance(name, str)
        self.action = kwds.get('action', self.__def_action)
        """The action of the form. This is the URL which will handle the form
        submit."""

        self.submit = kwds.get('submit', None)
        """The string on the submit button, or a tuple of strings if there are
        many."""
        if self.submit is None:
            self.submit = msg_registry['submit-button', 1]
        # Check the types.
        if isinstance(self.submit, (list, tuple)):
            for n in self.submit:
                if isinstance(n, tuple):
                    assert isinstance(n[1], msg_type)
                else:
                    raise RuntimeError("Internal error with submit types.")
        else:
            assert isinstance(self.submit, msg_type)
        assert self.submit

        assert isinstance(name, str)
        self.method = kwds.get('method', self.__def_method)
        "The submit method, GET or POST."

        self.encoding = kwds.get('encoding', self.__def_encoding)
        "The charset encoding that the form handler will accept."

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
        return [x.varname for x in self._fields]

    def labels( self, fieldnames=None ):
        """
        Returns a list of the labels of the fields.
        """
        if fieldnames is not None:
            fields = [self._fieldsmap[x] for x in fieldnames]
        else:
            fields = self._fields
        return [x.label for x in fields]

    def fetchnames( self, obj, exceptions=[] ):
        """
        Fetches attributes corresponding to the form field names from the given
        object 'obj' and returns a mapping with those values.  This can be
        useful if 'obj' is an object with the values that we want to fetch to
        initialize a map before rendering a form.

        Note: this does not use the field variable names, but rather the actual
        field names (in fact, this is one of the places where having a different
        name for the field and its associated variable may come in handy).
        """
        values = {}
        for field in self._fields:
            if field.name in exceptions:
                continue
            try:
                values[field.name] = getattr(obj, field.name)
            except AttributeError:
                pass
        return values

    def addfield( self, field ):
        """
        Add a field to the form. The field argument must be a Field instance.
        """
        if not isinstance(field, Field):
            raise TypeError('Expecting a Field instance.')
        if field.name in self._fieldsmap:
            raise RuntimeError(
                'Error: Field name %s is already used.' % field.name)
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
            try:
                fields = [self._fieldsmap[x] for x in only]
            except KeyError, e:
                raise RuntimeError(
                    "Error: field not present in form: %s" % str(e))

        # Remove fields to be ignored.
        if ignore is not None:
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


    def parse( self, args, only=None, ignore=None ):
        """
        Parse and validate the incoming arguments for the form.  The values of
        the parsed arguments are returned in a dict which is indexed by the
        field name (and not the variable name-- they are usually the same, but
        they may differ, see class Field).

        If there are errors, the parsed values are set as per the protocol for
        the specific fields (i.e. they *may* not return a settable replacement
        value if there is an error; if there is no replacement value passed
        along with the ValueError, the replacement value is always set to None).

        Therefore, a value for all the fields variable names is guaranteed to be
        present in the returned array, with values of None for those arguments
        that were not present.

        This form parsing code extracts ONLY the fields of args for which there
        are corresponding fields.  It uses the variable names specified on the
        fields for finding the values to be parsed.

        Note that this method is not really meant to be called from client code;
        you should instead make use of the FormParser, which provide support for
        common patterns for parsing arguments, which include possibly some
        client code for validating combinations of parsed arguments and error
        rendering.

        :Arguments:

          See the documentation for method Form.select_fields() for the meaning
          of the 'only' and 'ignore' arguments.

        :Return Values: a triple, consisting of

          - 'parsed_args' -> dict of str to parsed values: a dict of parsed
            arguments, each key being store as the varnames of the fields,
            including values for the arguments that failed to parse/validate, as
            set by the field.

          - 'errors' -> dict of str to str: a dict of field names to error
            messages for which there were errors (illegal values were supplied,
            the fields did not validate, required values, etc. It depends on the
            field type itself).

        If 'errors' is None, no error occurred.
        """
        fields = self.select_fields(only, ignore)

        # Initialize return values.
        parsed_args = {}
        errors = {}

        # For each selected field...
        for fi in self._fields:
            try:
                argvalue = args[fi.varname]

                # Internal sanity check, to make sure that values of None are
                # always set by use to indicate that an argument is missing,
                # then letting the fields deal with the specific meaning of that
                # themselves.
                assert argvalue != None

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

            elif isinstance(fi, FileUploadField):
                # Do nothing for file uploads, its encoding is separate.
                pvalue = argvalue

            elif isinstance(argvalue, str):
                # The value is a string, directly. Decode that.
                try:
                    pvalue = argvalue.decode(self.encoding)
                except UnicodeDecodeError, e:
                    # Broken client browser?  There is not much we can do if
                    # the browser cannot send the data in the appropriate
                    # encoding.
                    errors[fi.name] = msg_registry['error-invalid-encoding']

                    parsed_args[fi.name] = None
                    continue # Skip to next field.

            elif isinstance(argvalue, (list, tuple)):
                # The raw argument type is a list of strings.
                # Decode each string individually to unicode before parsing.
                vallist = []
                for val in argvalue:
                    try:
                        vallist.append(val.decode(self.encoding))
                    except UnicodeDecodeError, e:
                        # (Same decoding error as above.)
                        errors[fi.name] = msg_registry['error-invalid-encoding']

                        parsed_args[fi.name] = None
                        continue # Skip to next field.
                pvalue = vallist

            else:
                raise RuntimeError(
                    'Internal error with types: unexpected type: %s.' %
                    type(argvalue))

            # Now we check that we're always giving the field an expected value
            # type for the stuff to be parsed.
            #
            # Note that we do not make an exception for the None type, which
            # indicates that the value is absent (we let the field deal with
            # that situation itself), but the field must specify itself if it
            # can accept that situation (the answer should be yes, most of the
            # time, see the types_parse in each field).
            if not isinstance(pvalue, fi.types_parse):
                raise RuntimeError(
                    'Internal error with parse value type: %s.' % type(pvalue))

            #
            # Ask the field to parse the value itself.
            #
            try:
                dvalue = parsed_args[fi.name] = fi.parse_value(pvalue)

                # We check that the type of the parsed data value is one of the
                # expected types.
                assert isinstance(dvalue, fi.types_data)

            except ValueError, e:
                # There was an error parsing the field, i.e. the parsing raised
                # an invalid condition for that field. Pickup the error message,
                # and the value to be set instead, if given, via the second
                # attribute of the exception (see Field class for a description
                # of the protocol).
                #
                # Note: there is always a string specified for an error.
                if len(e.args) == 2:
                    msg, dvalue = e.args
                else:
                    msg, dvalue = str(e), None

                # Mark the error.
                errors[fi.name] = msg

                # Set the replacement value in the slot for the parsed value.
                parsed_args[fi.name] = dvalue

                # We check that the data type of the error replacement value is
                # a valid data type for that field.
                assert isinstance(dvalue, (type(None),) + fi.types_data)


        # Internal sanity check to make sure that we always fill an output for all
        # the checked fields.
        for fi in self._fields:
            assert fi.name in parsed_args

        if not errors:
            errors = None
        return parsed_args, errors


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
                    raise RuntimeError("Internal error with submit types.")
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
                        raise ValueError(
                            "Error: Multiple values for submits.")
                    found = sv
                    # Note: don't break, keep checking.

            return found

