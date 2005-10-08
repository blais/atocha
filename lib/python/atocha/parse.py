#!/usr/bin/env python
#
# $Id$
#

"""
Form parsing.

See class FormParser (below).
"""


# atocha imports.
from messages import msg_registry


__all__ = ['FormParser']

#-------------------------------------------------------------------------------
#
class FormParser(dict):
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

          fparser = FormParser(form, 'form_submit_url', cont=1)
          fparser.parse(args)

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

          fparser = FormParser(form, 'form_submit_url', args)

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

    Redirection
    -----------

    Data such as form errors and parsed data can be stored in session data for
    re-rendering the submitted form with errors, if that is how the framework is
    intended to work. You can decide.  This, and redirection, is delegated to a
    concrete class for specific implementation.

    See the methods below for more details.
    """

    __generic_status = 'error-invalid-input'
    __generic_status_many = 'error-many'

    def __init__( self, form, redirurl=None,
                  args=None, end=False,
                  process=None ):
        """
        Create a parser with the given form, and error redirection URL.

        :Arguments:

        - 'form' -> instance of Form: the form definition for the variables
          we're parsing.

        - 'redirurl' -> str: a URL to which we should redirect to if an error is
          detected.  If it is not given, the referer URL is used.

        - 'args' -> dict of str (optional): a mapping of the submit query
          arguments that are sent from the client.  We are expecting that the
          types of values of this map will be one of str, a list of str, or a
          special object for file uploads.

        - 'end' -> bool (optional): if 'end' is True, this constructor will
          check immediately for errors and perform redirection automatically.
          This parameter is not useful if the args are not specified (we have
          not sent anything to be parsed).

          If you have some custom argument checking code, you should specify
          end=False to CONTINUE the checking protocol and eventually call the
          end() method.

          Note: if you continue and you never eventually call end(), an assert
          will go off when this object is destroyed.  This insures that the
          client code never forgets to complete the checking protocol.

        - 'process' -> instance: an object that will get called to process the
          redirection. If this is not set, we ask a concrete implementation of
          this class to perform the redirection.

        """

        self._form = form
        "The form instance that we're parsing."
        
        self._redirurl = redirurl
        "The URL to redirect to for errors."
        
        self._errors = {}
        """A dict of field names to error field messages. The error messages are
        specific to the fields to by they are referred and are meant to be
        rendered near the corresponding input after a redirection to the
        original form."""

        self._status = None
        "A string that indicates the general error status."
        
        self._message = u''
        """A unicode string that is meant to tell the user globally about the
        errors to be fixed."""

        self._submit = None
        """A string, which is set after parsing, which indicates which of the
        submitted buttons was used to submit the form.  This is only meaningful
        if the form has multiple submit buttons."""

        self._submit_parsed = False
        "A flag which is set after the submit values have been parsed."
        
        self._ended = False
        """A flag which is set after the client has invoked the end of parsing.
        This is used internally to insure that a parser always gets completed
        properly."""

        self._process = process or self.do_redirect
        """An object that will get called to process the redirection with the
        form status, message, errors and partially parsed values for rerendering
        the form to the user with errors marked explicitly."""

        # Parse the arguments at creation if they are given to us.
        if args:
            self.parse(args)

        # Complete the parsing if it is requested.
        if end:
            self.end()


    def __del__( self ):
        """
        Destructor override that just makes sure that we ended the parser.
        """
        dict.__del__(self)
        if not self._ended:
            raise RuntimeError("Form parser not ended properly.")


    def parse( self, args, only=None, ignore=None ):
        """
        Parse the form with the given arguments, including the submit value if
        necessary. This parses all the arguments for which a corresponding field
        exists with a varname in args, using the field's code and type
        conversion, and sets it on this object.

        Args for which no corresponding field exist are not parsed, converted
        nor copied in the parser, they are simply left for the client to process
        from args manually.

        :Arguments:

          - 'args' -> dict of str to str: for each field varname, contains a str
            in the form's specified encoding for the unparsed submitted value
            for that field.
  
          See the documentation for method Form.select_fields() for the meaning
          of the 'only' and 'ignore' arguments.

        """

        # Parse the arguments using the form parsing algorithm.
        parsed_args, errors = self._form.parse(args, only, ignore)

        # If there were errors...
        if errors is not None:
            assert errors

            # Indicate errors, with a specific status.
            self.error(status=self.__generic_status, **errors) 

        # Update our parsed values stored with the parsed args.
        self.update(parsed_args)

        self.parse_submit(args)

    def parse_submit( self, args ):
        """
        Parse only for the submit value and nothing else.
        """
        # Parse the value of the various submit buttons if there are many.
        self._submit = self._form.parse_submit(args)
        self._submit_parsed = True
        return self._submit

    def getsubmit( self ):
        """
        Returns the value of the submitted button.  This is None if there is
        only a single submit button in the form, or a str with the appropriate
        value of the button with which the form was submitted.
        """
        # Make sure that we parsed before we access this value.
        assert self._submit_parsed
        return self._submit

    def getargs( self ):
        """
        Returns a copy of the parsed arguments (dict).  This is intended as a
        convenience if you need to store or pass around the arguments, rather
        than having to pass the parser itself.

        Also, the returned value does not include the unset values.  If you
        access a value on the parser, you have a guarantee that it is at least
        set to None to indicate that there is no value.  (This is a convenience
        for all the parsing code.)  The returned dict from this method instead
        removes those items which are None.  This is meant to minimize the
        amount of formdata that gets stored between requests, if there is an
        error.
        """
        args = {}
        for k, v in self.iteritems():
            if v is not None:
                args[k] = v
        return args

    def haserrors( self ):
        """
        Returns true if some errors have already been signaled.
        """
        return bool(self._errors)
        
    def geterrors( self ):
        """
        Returns the accumulated errors (a dict of str to str, field names to
        field-specific error message).  This can be used by the form renderer to
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


    def error( self, message=None, status='error', errors=[], **kwds ):
        """
        Adds an error to the current state.

        :Arguments:

        - 'message' -> str: is the global error message to be used for this set
          of errors, if and only if there is no other error set.

        - 'status' -> str (optional, default is 'error'): is the global error
          status to be used for this set of errors, if and only if there is no
          other error set, in which case a generic error status will be set.

        - 'errors' -> list of str: field names which should be marked as
          erroneous, without a specific error message.  A generic error message
          will be substituted automatically, such as 'Invalid value.'.

        The keyword arguments identify which fields are erroneous. They can be
        set to True or 1, or to a specific error message for that field.

        Note that the 'message' is intended to be used only if the errors given
        in this call will be the only errors signaled during the entire parsing.
        If this method is called more than once, a generic error message is
        substituted, such as 'Please fix errors.'
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
            self._status = status
            self._message = message or msg_registry['generic-ui-message']

        #
        # Update errors.
        #

        # Merge the errors in the keywords (we'll check everything below).
        for e in errors:
            assert isinstance(e, str)
            assert e not in kwds
            kwds[e] = True

        # Do some checking and setting for the keywords.
        for fname, errmsg in kwds.iteritems():
            # Check that the fieldname exists in the form.
            assert self._form[fname]

            if not isinstance(errmsg, (unicode, int, bool)):
                raise RuntimeError(
                    "Error: invalid encoding for error message: %s" %
                    repr(errmsg))

            # Substitute a message for the specific error, a generic error
            # message, if there isn't one.
            if isinstance(errmsg, (int, bool)):
                errmsg = msg_registry['generic-value-error']
            assert isinstance(errmsg, unicode)

            # Update our error messages with the given error.
            self._errors[fname] = errmsg


    def end( self, redirurl=None, redirect=None ):
        """
        Completes the validation phase, redirecting if necessary.
        Redirection is performed is an error was signaled.

        :Arguments:

        - 'redirurl' -> str (optional): can be used to override the default
          redirection URL.

        - 'redirect' -> bool: can be used to force redirection even if there was
          no error (i.e. a warning qualifies).

        Returns True after redirection, if it returns (redirection should work
        better by raising an exception, so it is possible that this method never
        returns.)  If no redirection is done, returns False.
        """
        # Mark the parser protocol as complete.
        self._ended = 1

        # If we have errors, redirect to be rendered with errors.
        if self.haserrors():
            rurl = redirurl or self._redirurl

            # Note: we do not make sure that at some point a redirection URL was
            # specified.  Within the specific framework where thi sis getting
            # used, there might be a way to automatically get the referer of the
            # page and to automatically redirect to that.  By not including the
            # following check, it is possible to leave the redirection URL unset
            # and to use that state as a way to let the processor find the
            # referer.
            # assert rurl

            # Make sure that a status and a message have been set.
            assert self._status
            assert self._message
            
            # Delegate to the derived class to redirect.
            return self._process(
                rurl, self._form, self._status, self._message,
                self._errors, self.getargs())

        # Otherwise just return and let the client code finish its actions.
        return False


    def do_redirect( self, url, form, status, message, errors, args ):
        """
        Perform a requested error redirection.  Override this method to
        implement this functionality, whose details depend on the framework that
        is being used.  You can also specify the process argument to the
        constructor if you prefer to do that.
        """
        return True





