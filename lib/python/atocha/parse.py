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
Form parsing.

See class FormParser (below).
"""

# atocha imports.
import atocha
from fields.uploads import FileUpload
from messages import msg_registry


__all__ = ['FormParser']


#-------------------------------------------------------------------------------
#
class FormParser:
    """
    Helper class that allow us to parse a form's arguments and process and
    generate errors, including a protocol that let's the user add some
    customized inter-variable or other checks.

    An instance of this class oversees the general process of parsing arguments
    and maintains the error and parsing state.  With the form fields, stores the
    parsed values and accumulates error state and messages.  It is used to
    accompany validation and parsing of the arguments in handlers.  This object
    is meant to implement the following code pattern in the code that handles
    the submit:

    1. Parse the arguments according to the field types, doing the necessary
       conversions, e.g.::

          fparser = FormParser(form, 'form_submit_url')
          fparser.parse_args(args)

    2. Do manual validation of fields via custom code::

          if fparser['valmin'] > fparser['valmax']:
              fparser.error('Invalid value ordering', 'error-invalid',
                            valmin='Larger than maximal value',
                            valmax='Smaller than mininal value')

       There are many different variants that can be used to call the error
       notification, see the error() documentation for details.

    3. Redirect if errors or warnings (specify a point at which arguments are
       considered to have been fully parsed)::

          fparser.end()

    4. Finish handler code (do something with the accepted data).

    Alternatively, you can do all the parsing and redirection in one line of
    code if you don't have any custom parsing to do::

          fparser = FormParser(form, args, 'form_submit_url', end=1)

    State of the Parser
    -------------------

    The state managed by this parser consists in the following data:

    - Parsed Data -> dict of str to data values: parsed data (available directly
      on this object, the parser is a dict container itself) for each of the
      defined field names.  The types of the value depend on the kinds of fields
      that the form contains.

    - UI message -> str: a message that should be printed, globally, for all the
      fields at once, upon redirecting with errors.  This is intended to be a
      single message return to the client describing what has to be fixed.

      If this is not set OR if there are multiple errors, a generic error
      message is substituted automatically, such as `Please fix errors.'.

    - Status -> str: a short client-defined string that indicates the status of
      parsing.  This can be used like the UI message by client code to return a
      programmable meaning to the client browser, and is used to help automate
      parsing of the response during automated testing.  For example, I use this
      field to fill a 'status' meta tag with it, and automated test code fetches
      this status everytime and compares it to expected values.

    - Errors -> dict of str to str: a mapping of field names to error messages
      (or bool).  If the value of an error is a msg_type object, then it is
      meant to be used as an error message to be rendered near the input field
      when the form gets redirected.  If it is a bool, then the error is
      generic.  Generic errors will have their message automatically replaced by
      a generic message, such as `Invalid value.'.

    - Submit value -> str or None: if there are multiple submit buttons in the
      form, the parser automatically detects which one it was called with, and
      stores that value specially as the 'submit value'.  You can then decide to
      take whichever action is necessary in the handler code, by accessing this
      value with getsubmit().

    Configuring Redirection
    -----------------------

    Data such as form errors and parsed data can be stored in session data for
    re-rendering the submitted form with errors, if that is how the frameworks
    are intended to work. You must decide how to implement the specifics of this
    process.  Redirection with the appropriate data is thus delegated to a
    concrete class for specific implementation.  There are four ways to tell the
    framework how this should happen, in decreasing order of preference:

    1. You derive from this class and override do_redirect().  Then you
       instantiate your derived class instead of this one;

    2. You configure the redirect_func class attribute on this class after
       importing it in the Python environment. This should work for the entire
       duration of the Python interpreter;

    3. You specify 'redirfun' in the constructor, an object that will get called
       when the for redirection;

    4. You do nothing and call end() manually everytime, examining its return
       value and take appropriate action if you need to redirect.  Note that if
       you choose this, you cannot use the end option in the constructor (there
       is no way to return the result value of ending the parser);

    For methods 1, 2 and 3, we expect redirection to be implemented using an
    exception.
    """

    __generic_status = 'error-field'
    __generic_status_many = 'error-many'

    # Function called to perform redirection if present.
    redirect_func = None

    # Object that will get called to normalize the types before parsing.  This
    # is used to adapt the incoming arguments from a variety of web application
    # frameworks to the kinds of generic arguments that this library is
    # expecting.
    normalizer = None


    def parse( form, args, redir=None, redirfun=None ):
        """
        Creates a FormParser, applies the arguments to be parsed, and completes
        the parser automatically, return the parsed results if there is no
        error.  This method performs redirection automatically if there were
        errors, or returns None if no redirection protocol has been configured.

        This is essentially the simpler and preferred way to parse arguments, if
        you have no custom code for additional validation.  Otherwise, you
        should create a form parser yourself and use its various methods to
        perform the parsing.
        """
        # Create a parser.
        parser = FormParser(form, redir=redir, redirfun=redirfun)

        # Parse the given arguments.
        parser.parse_args(args)

        # Complete the parsing.
        return parser.end()

    parse = staticmethod(parse)


    def __init__( self, form, args=None, redir=None, redirfun=None ):
        """
        Create a parser with the given form, and error redirection URL.

        :Arguments:

        - 'form' -> instance of Form: the form definition for the variables
          we're parsing.

        - 'redir' -> str: a URL to which we should redirect to if an error is
          detected.  If automatic redirection is to be used (the normal case),
          this should always be specified.

        - 'args' -> dict of str (optional): a mapping of the submit query
          arguments that are sent from the client.  We are expecting that the
          types of values of this map will be one of str, a list of str, or a
          special object for file uploads.

        - 'redirfun' -> instance: an object that will get called to process the
          redirection. See docstring above for alternatives on this.
          (Specifying the 'redirfun' here is not the most convenient way to do
          this.)

        If you have some custom argument checking code, you should specify call
        this constructor directly to continue the validation protocol and
        eventually call the end() method.  This is the way that you're supposed
        to handle constraints between two different fields, with custom code on
        the caller side.

        If you continue and you never eventually call end(), an assert or trace
        will go off when this object is destroyed.  This insures that the client
        code never forgets to complete the checking protocol.

        Note that if you do not have custom code to write, you should use the
        FormParser.parse() method that takes the same parameters and does all
        the steps automatically and returns the parsed values.
        """

        assert form is not None
        self._form = form
        "The form instance that we're parsing."

        self._redirurl = redir
        "The URL to redirect to for errors."

        self._values = {}
        """A dict of the successfully parsed values of the arguments.  Arguments
        which had errors are not present in this dict.  The names correspond to
        the field names and there may be some extra data stored via the store()
        method."""

        self._errors = {}
        """A dict of field names to errors in the form of (message,
        repl_rvalue). The error messages are specific to the fields to by they
        are referred and are meant to be rendered near the corresponding input
        after a redirection to the original form."""

        self._status = None
        "A string that indicates the general error status."

        self._message = u''
        """A unicode string that is meant to tell the user globally about the
        errors to be fixed."""

        self._submit = None
        """A list containing a single element of type str, which is set after
        parsing, which indicates which of the submitted buttons was used to
        submit the form.  This is only meaningful if the form has multiple
        submit buttons."""

        self._submit_parsed = False
        "A flag which is set after the submit values have been parsed."

        self._ended = False
        """A flag which is set after the client has invoked the end of parsing.
        This is used internally to insure that a parser always gets completed
        properly."""

        if redirfun is not None:
            self.redirect_func = redirfun
        """An object that will get called to process the redirection with the
        form status, message, errors and partially parsed values for rerendering
        the form to the user with errors marked explicitly."""

        self._accessor = self.o = ParserAccessor(self)
        """Accessor helper class which is used to get access to the values via
        an attribute interface.  Access via references to 'parser.o'."""

        # Parse the arguments at creation if they are given to us.
        if args is not None:
            self.parse_args(args)

    def __del__( self ):
        """
        Destructor override that just makes sure that we ended the parser.
        """
        if atocha.completeness_errors:
            if not self._ended:
                raise atocha.AtochaDelError("Form parser not ended properly.",
                                            self._form.name)


    def parse_args( self, args, only=None, ignore=None ):
        """
        Parse and validate the incoming arguments for the form, including the
        submit value if necessary. This parses all the arguments for which a
        corresponding field exists with a corresponding 'varname' in args, using
        the field's code and type conversion, and sets it on this object.

        The values of the parsed arguments are available as a dict interface on
        this object which is indexed by the field name (and not the variable
        name 'varname'-- they are usually the same, but they may differ, see
        class Field for details).

        A value for all the fields variable names is guaranteed to be accessible
        on this object, with values of None for those arguments that were not
        present.

        If there are errors, the replacement values to be used for re-rendering
        are set by the fields themselves (i.e. the fields *may* not have
        returned a usable replacement value if there is an error).

        Arguments for which no corresponding field exist are ignored--they are
        not parsed, converted nor copied in the parser, they are simply left for
        the client to process from args manually.

        :Arguments:

          - 'args' -> dict of str to str: for each field varname, contains a str
            in the form's specified encoding for the unparsed submitted value
            for that field.

          See the documentation for method Form.select_fields() for the meaning
          of the 'only' and 'ignore' arguments.

        :Return Values: None.  All the parsed data is available on this object.
        """

        # Normalize the submitted arguments if required.
        if self.normalizer:
            args = self.normalizer.normalize(args)
        assert isinstance(args, dict)

        # Select the fields.
        fields = self._form.select_fields(only, ignore)

        # Parse the arguments using the form parsing algorithm.
        for fi in fields:
            has_error, retvalue = self._form.parse_field(fi, args)
            if has_error == 0:
                # Accept this parsed value.
                self._values[fi.name] = retvalue
            elif has_error == 1:
                # Check the types of the returned values.
                message, repl_rvalue = retvalue
                assert repl_rvalue is None or \
                       isinstance(repl_rvalue, fi.types_render)

                # Indicate an error.
                #
                # Use generic status for errors.  Maybe in the future a field
                # error will be able to indicate a specific status as well.
                #
                # Note: if there is a single error, we could decide to use the
                # error's message for the UI message.
                self.error(**{'_status': self.__generic_status,
                              fi.name: retvalue})

        # Parse the submit buttons.
        self.parse_submit(args)

    def parse_submit( self, args ):
        """
        Parse only for the submit value and nothing else.
        """
        # Parse the value of the various submit buttons if there are many.
        submit_value = self._form.parse_submit(args)
        self._submit = submit_value
        self._submit_parsed = True

        return submit_value

    def getsubmit( self ):
        """
        Returns the value of the submitted button.  This is None if there is
        only a single submit button in the form, or a str with the appropriate
        value of the button with which the form was submitted.
        """
        # Make sure that we parsed before we access this value.
        assert self._submit_parsed
        return self._submit

    def __getitem__( self, fname ):
        """
        Access the parser's parsed values, insuring that values which have not
        been parsed simply return None rather than raising an exception.  This
        is just a convenience. We recommend that you instead use the accessor
        object where you can access the parsed values via attribute names.
        """
        try:
            return self._values[fname]
        except KeyError:
            # Check if the name is valid.
            try:
                fi = self._form[fname]
                return None
            except KeyError:
                raise KeyError("Invalid field name '%s'." % fname)

    def __setitem__( self, fname, value ):
        """
        See store() method.
        """
        return self.store(fname, value)

    def __contains__( self, fname ):
        """
        Membership test.
        """
        return fname in self._values

    def store( self, name, value ):
        """
        Store some extra data that is not associated with any field, but that
        will get routed through the form data system if an error occurs.

        In exceptional cases, this can also be used to replace the kind of data
        that will be used to fill a field on re-render, use with care.

        This is useful if your fields have some extra state that needs to be
        kept in parallel with the state in the widgets.  The (name, value) pair
        is stored along with the values dictionary, and therefore the name must
        not coincide with a valid field name.
        """
        # Do not check that the fieldname does not exist in the form.
        # assert name not in self._form.names()

        # Store along with the values dict.
        self._values[name] = value

    def clear( self, name ):
        """
        Clear the given value.
        """
        try:
            del self._values[name]
        except KeyError:
            pass

    def getvalues( self, cullfiles=False ):
        """
        Returns the parsed arguments (dict).  This is intended as a convenience
        if you need to store or pass around the arguments, rather than having to
        pass the parser itself.

        Also, the returned value does not include the unset values.  If you
        access a value on the parser, you have a guarantee that it is at least
        set to None to indicate that there is no value.  (This is a convenience
        for all the parsing code.)  The returned dict from this method instead
        removes those items which are None.  This is meant to minimize the
        amount of formdata that gets stored between requests, if there is an
        error.

        If 'cullfiles' is True, the files resulting from a FileUpload are culled
        automatically. This is meant to be useful for passing around formdata
        that can be potentially be serialized.
        """
        # Make a copy of the values to be returned and remove all the file
        # uploads parsed values, because we won't be able to fill the file
        # widget with the uploaded data, it would not make sense.
        #
        # Note: we make sure to also copy the extra values data that was added
        # via the store() method.
        if not cullfiles:
            # Note: we don't return a copy for efficiency and because we think
            # that at that point the user will not use the parser anymore, so
            # sharing the object should be fine.
            return self._values
        else:
            vcopy = self._values.copy()
            for name, val in self._values.iteritems():
                if isinstance(val, FileUpload):
                    try:
                        del vcopy[name]
                    except KeyError:
                        pass
            return vcopy

    def ok( self, fieldname ):
        """
        Returns false if the given field has an error associated to it.
        See haserror() below.
        """
        return fieldname not in self._errors

    def haserror( self, fieldname ):
        """
        Returns true if the given field has an error associated to it.
        See ok() above.
        """
        return fieldname in self._errors

    def haserrors( self ):
        """
        Returns true if some errors have already been signaled.
        """
        return bool(self._errors or self._message or self._status)

    def geterrors( self ):
        """
        Returns the accumulated field errors, a dict of (message, repl_rvalue)
        tuples for each field name.  This can be used by the form renderer to
        render the errors near the corresponding input values in the HTML form.
        """
        return self._errors

    def geterrorfields( self ):
        """
        Returns a list of the fields which have had errors (a list of str):
        """
        return self._errors.keys()

    def geterrorlabels( self ):
        """
        Returns a list of the labels of the fields which have had errors.
        """
        # Note: this should always work, unless an error would be specified for
        # a field that is not in the form, which would be an error.
        return [self._form[x].label for x in self._errors.iterkeys()]


    def _normalize_error( error ):
        """
        Normalize the type of an error to a (message, repl_rvalue)
        triple.
        """
        if isinstance(error, (int, bool)):
            # Substitute a message for the specific error, a generic error
            # message, if there isn't one.
            error = (msg_registry['generic-value-error'], None)
        elif isinstance(error, unicode):
            error = (error, None)
        elif isinstance(error, tuple):
            assert len(error) == 2
        else:
            raise atocha.AtochaError(
                "Error: invalid type for error message: %s" %
                repr(error))
        return error
    _normalize_error = staticmethod(_normalize_error)

    def error( self, _message=None, _status='error', _names=[], **kwds ):
        """
        Adds an error to the current state.

        :Arguments:

        - '_message' -> str: is the global error message to be used for this set
          of errors, if and only if there is no other error set.

        - '_status' -> str (optional, default is 'error'): is the global error
          status to be used for this set of errors, if and only if there is no
          other error set, in which case a generic error status will be set.

        - '_names' -> list of str: field names which should be marked as
          erroneous, without a specific error message nor replacement values.  A
          generic error message will be substituted automatically, such as
          'Invalid value.'.

        The keyword arguments identify which fields are erroneous. They can be
        set to True or 1, or to a specific error message for that field, or to a
        (message, repl_rvalue) tuple.

        Note that the 'message' is intended to be used only if the errors given
        in this call will be the only errors signaled during the entire parsing.
        If this method is called more than once, a generic error message is
        substituted, such as 'Please fix errors.'

        Also, you can signal an error without specifying any error fields if you
        do not have field-specific messages to indicate.  This will still put
        the parser in an error state.
        """

	# If there are already errors...
        if self.haserrors():
            # Set the status and error message to indicate many errors.
            self._status = self.__generic_status_many
            self._message = msg_registry['generic-ui-message']
        else:
            # Set the current status and message as given.
            assert self._status is None
            assert self._message == u''
            self._status = _status
            self._message = _message or msg_registry['generic-ui-message']
        # Note: the above marks the parser as having had errors, even if there
        # are no field-specific error messages. See haserrors().

        #
        # Update errors.
        #

        # Merge the errors in the keywords (we'll check everything below).
        for e in _names:
            assert isinstance(e, str)
            assert e not in kwds
            kwds[e] = True

        # Do some checking and setting for the keywords.
        for fname, error in kwds.iteritems():
            # Check that the fieldname exists in the form.
            assert self._form[fname]

            # Make sure that the error is a triple.
            error = self._normalize_error(error)

            # Update our error messages with the given error, where error is
            # necessarily a (message, repl_rvalue) tuple.
            self._errors[fname] = error

    def clear_errors( self, *names ):
        """
        Clear the errors associated with the given fields.
        """
        for name in names:
            try:
                del self._errors[name]
            except KeyError:
                pass

        if not self._errors:
            self._status, self._message = None, u''

    def clear_message( self ):
        """
        Clear the UI message that is to be displayed for errors.
        """
        self._message = u''

    def set_redirect( self, redir ):
        """
        (Re-)Set the redirection URL.
        """
        self._redirurl = redir


    def end( self, redir=None ):
        """
        Completes the validation phase, redirecting if necessary.
        Redirection is performed is an error was signaled.

        :Arguments:

        - 'redirurl' -> str (optional): can be used to override the default
          redirection URL.

        If there is an error...

        - This function calls the redirect() method, which is supposed to have
          been customized to implement the actual work of redirection.

        - Most often this works by raising an exception.  If there is no such
          customization, this method will be allowed to return 'None' (or the
          value of the redirect function) and the caller can check this to
          perform the redirection manually if necessary.

        If there is NO error...

        - This method returns an instance which has its attributes set to the
          final parsed values of the fields, using the field names.  If a value
          is missing, it is simply set to None, so it is always guaranteed to be
          present.

        """

        # Mark the parser protocol as complete.
        self._ended = 1

        # If we have errors, redirect to be rendered with errors.
        if self.haserrors():
            return self.redirect(redir)

        # Otherwise just return the accessor instance, which is initialized with
        # the appropriate values.  This works similarly to optparse.
        return self._accessor

    def cancel( self ):
        """
        Cancel this parser.  It is important to use this method if you have not
        called end() on a parser when you do not intend to later end() it,
        because otherwise it will raise an assert to alert you that your parsing
        was not complete.
        """
        self._ended = 1  # Mark as ended.

    def redirect( self, redir=None ):
        """
        Force redirection.  To be able to redirect, the parser must be
        complete/ended.
        """
        assert self._ended

        # Note: we do not make sure that at some point a redirection URL was
        # specified.  Within the specific framework where this is getting used,
        # there might be a way to automatically get the referer of the page and
        # to automatically redirect to that.  By not including the following
        # check, it is possible to leave the redirection URL unset and to use
        # that state as a way to let the processor find the referer.  assert
        # rurl

        # Delegate to the derived class to redirect.
        fun = self.redirect_func
        if fun is None:
            fun = self.do_redirect

        rurl = redir or self._redirurl

        return fun(rurl, self._form, self._status, self._message,
                   self.getvalues(True), self._errors)

    def do_redirect( url, form, status, message, values, errors ):
        """
        Perform a requested error redirection.  Override this method (static) to
        implement this functionality, whose details depend on the framework that
        is being used.  You can also specify the process argument to the
        constructor if you prefer to do that.
        """
        # Default mechanism, return this value from end() method.
        return None

    do_redirect = staticmethod(do_redirect)


#-------------------------------------------------------------------------------
#
class ParserAccessor(object):
    """
    Accessor helper class that allows you to access the contents of the
    values via its attributes.
    """
    def __init__( self, parser ):
        self._parser = parser
        """Parser (cyclic dependency, unfortunately)."""

    def __getattr__( self, fname ):
        return self._parser.__getitem__(fname)

    def getsubmit( self ):
        return self._parser.getsubmit()

    def getvalues( self ):
        return self._parser.getvalues()

