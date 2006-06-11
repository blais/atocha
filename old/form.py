#!/usr/bin/env python
#
# $Source: /home/blais/repos/cvsroot/hume/app/lib/hume/form.py,v $
# $Id: form.py,v 1.44 2005/05/30 20:57:29 blais Exp $
#
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
Server-side form handling library.

This is a library that provides classes for representing forms, that can then be
used for rendering the form, parsing and converting the types in the handler.

There are mainly four components:

1. Form class: container of widgets, and global parameters for the entire form
   (submit buttons, actions, method, etc.);

2. Field classes: a hierarchy of classes that represent various types of
   inputs.  These are akin to widgets in a desktop UI toolkit;

3. FormRenderer: a class that knows how to render all the widgets appropriately.
   There can be various implementations of this renderer, for example, one that
   renders directly to HTML text, and one that builds a tree of widgets.  You
   can also build a renderer class that renders not to a form, but to
   displayable values only;

4. FormParser: a helper class that supports the code patterns needed to handle
   forms and parse its arguments, and return and render appropriate error
   messages.

For each widget in a form, at various points the data that moves through them is
of three different types:

- the 'data' type, which is the final Python type that we want to read;
- the 'render' type, a type that is suitable for rendering purposes by renderer;
- the 'parse' type, the type of data that is submitted by forms to a browser, to
  be parsed into the 'data' type.


"""



# Note: rendering radio buttons that have no default value currently initializes
# without a selection (invalid to submit).

## FIXME TODO add disabled status support
## FIXME TODO add support for accept types for fileupload field
## FIXME TODO fix list types, they don't work quite right

## FIXME TODO: answer this question: what happens when the value is not passed
##             in via the args?  Do we just set the default value?  Default
##             value should always be None to signal that no input was provided,
##             unless provided by the widget initialization code.

## FIXME: the renderer needs to whine about the user asking to render fields
##        that do not exist in it.

## FIXME: you need to specify what happens to args fields for which there are no
## corresponding widgets available.  For example, how do we deal with locations?


#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

# stdlib imports
import types, re, datetime, StringIO


#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

_strtype = types.UnicodeType
_dec_encoding = 'iso-8859-1'

#===============================================================================
# PUBLIC DECLARATIONS
#===============================================================================

__all__ = [
    'StringField', 'PasswordField', 'TextAreaField', 'EmailField',
    'IntField', 'FloatField', 'BoolField',
    'RadioField', 'ListField', 'MenuField',
    'DateField', 'ActiveDateField',
    'FileUploadField',
    'FormError', 'Form',
    'BaseRenderer', 'SimpleRenderer',
    'tr_noop', 'handle_upload',
    'TestFields',
    ]

#===============================================================================
# ABSTRACT FIELD
#===============

#-------------------------------------------------------------------------------
#
class NoDef:
    """Dummy class used for a non-specified optional parameter."""
    pass

#-------------------------------------------------------------------------------
#
class Field:
    """
    Base class for all form fields.

    One particularity of forms is that values which are not present in the
    submit data are assumed to take on the value of 'default'.

    Each field must be given at least a name unique within the form.

    Optional fields:

    - 'label': a label can be specified that is used to render the form, if that
      is used.  If 'label' is None, the field is rendered as a hidden input;

    - 'default': Every widget has a default value automatically set, this is
      because inputs for which the data is empty are not submitted by browsers.
      This keyword option can be used to specify an alternate default value;

    - 'notnull': indicates that the input value cannot be null at the moment it
      is being parsed.  If this option is set, an exception is raised if upon
      parsing.  If it is not set, after parsing the parsed value will contain the
      value of 'default'.

    Notes:

    - hidden fields are specified by setting 'label' to None;

    """

    def __init__(self, name,
                 label=None, default=None, notnull=None):
        self.name = name
        assert isinstance(name, str)
        self.label = label
        assert label is None or type(label) in types.StringTypes
        self.default = default
        self.notnull = notnull
        self.validators = []

    def __str__(self):
        return "<Field name=%s>" % self.name

    def ishidden(self):
        """
        Returns true if this field is hidden.
        """
        return self.label is None

    def prepare_value(self, value):
        "Prepare the value for rendering."
        return value

    def parse(self, value):
        return value

#===============================================================================
# CONCRETE FIELDS
#================

#-------------------------------------------------------------------------------
#
class TextField(Field):
    """
    Verify that the field is a string.
    This is a base class.
    """

    class_ = 'text'

    def __init__(self, name,
                 label=None, default=None, notnull=None, 
                 minlen=None, maxlen=None, ascii=False):
        Field.__init__(self, name, label, default, notnull)
        self.minlen = minlen
        self.maxlen = maxlen
        self.ascii = ascii

    def parse(self, value):
        if not isinstance(value, _strtype):
            raise ValueError
        if self.minlen is not None and len(value) < self.minlen:
            raise ValueError
        if self.maxlen is not None and len(value) > self.maxlen:
            raise ValueError
        return value

#-------------------------------------------------------------------------------
#
class StringField(TextField):
    """
    Verify that the field is a single line string. The value that is returned is
    a string with leading and trailing whitespace stripped off.  This field can
    be used to accept both Unicode and encoded strings.
    """

    class_ = 'string'

    def parse(self, value):
        if not isinstance(value, _strtype):
            raise ValueError
        value = value.strip()
        if self.minlen is not None and len(value) < self.minlen:
            raise ValueError
        if self.maxlen is not None and len(value) > self.maxlen:
            raise ValueError

        if self.ascii:
            try:
                value = value.encode('ascii')
            except UnicodeEncodeError:
                raise ValueError
        else:
            for ch in value:
                o = ord(ch)
                if o < 0x20: # or o > 0x80: we accept unicode but no special chars.
                    raise ValueError
        return value

#-------------------------------------------------------------------------------
#
class EmailField(StringField):
    """
    Field for an email address.  Parses into a non-Unicode string.
    """

    class_ = 'email'

    vchars = '[a-zA-Z0-9\._\-]'
    mre = re.compile('^%s+@%s+\.%s+$' % (vchars, vchars, vchars))

    ascii = True

    def parse(self, value):
        value = StringField.parse(self, value)
        if not self.mre.match(value):
            raise ValueError
        try:
            value = value.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError
        return value

#-------------------------------------------------------------------------------
#
class TextAreaField(TextField):
    """
    Verify that the field is a possibly multiline-string.

    (This corresponds to a text area.)
    """

    class_ = 'textarea'

    def __init__(self, name,
                 label=None, default=None, notnull=None, 
                 minlen=None, maxlen=None, rows=None, cols=None):
        TextField.__init__(self, name, label, default, notnull)
        self.rows = rows
        self.cols = cols

#-------------------------------------------------------------------------------
#
class PasswordField(TextField):
    """
    Password field.
    """

    def prepare_value(self, value):
        return None # automatically hide password values before rendering.
        ## Note: this should only be done when we're not using https.

#-------------------------------------------------------------------------------
#
class IntField(Field):
    """
    Verify that the field contains a valid integer. The returned value
    is a Python integer.
    """

    class_ = 'int'

    def __init__(self, name,
                 label=None, default=None, notnull=None, 
                 minval=None, maxval=None):
        Field.__init__(self, name, label, default, notnull)
        self.minval = minval
        self.maxval = maxval

    def parse(self, value):
        if not isinstance(value, _strtype):
            raise ValueError
        value = int(value)
        if self.minval is not None and value < self.minval:
            raise ValueError
        if self.maxval is not None and value > self.maxval:
            raise ValueError
        return value

#-------------------------------------------------------------------------------
#
class FloatField(Field):
    """
    Verify that the field contains a valid floating point number. The
    returned value is a Python float.
    """

    class_ = 'float'

    def __init__(self, name,
                 label=None, default=None, notnull=None, 
                 minval=None, maxval=None):
        Field.__init__(self, name, label, default, notnull)
        self.minval = minval
        self.maxval = maxval

    def parse(self, value):
        if not isinstance(value, _strtype):
            raise ValueError
        value = float(value)
        if self.minval is not None and value < self.minval:
            raise ValueError
        if self.maxval is not None and value > self.maxval:
            raise ValueError
        return value

#-------------------------------------------------------------------------------
#
class BoolField(Field):
    """
    A single boolean (checkbox) field.
    """

    class_ = 'bool'

    def parse(self, value):
        if type(value) in types.StringTypes:
            if value in ['0', 'False']:
                return False
            elif value in ['1', 'True']:
                return True
        # booleans and any other string
        return bool(value)

    def prepare_value(self, value):
        return bool(value)

#-------------------------------------------------------------------------------
#
# Choices
# -------
#
# exactly 1 : radio buttons or menu (without multiple option)
#     <input name='name' type='radio' value='1'/>
#     <input name='name' type='radio' value='2'/>
#     <input name='name' type='radio' value='3'/>
#
#     <select name='name'>
#     <option value='1' />
#     <option value='2' />
#     <option value='3' />
#     </select>
#
# 0 or many: checkboxes or menu (with multiple option)
#     <input name='name' type='checkbox' value='1'/>
#     <input name='name' type='checkbox' value='2'/>
#     <input name='name' type='checkbox' value='3'/>
#
#     <select name='name' multiple='1' size='3'>
#         <!-- size has to be >1 if multiple is used -->
#     <option value='1' />
#     <option value='2' />
#     <option value='3' />
#     </select>

#-------------------------------------------------------------------------------
#
class MultipleField(Field):
    """
    Choices among many.

    'values' can be either a list or a mapping, the latter case maps from values
    to labels to be used for rendering.

    This is only a base class for radio buttons, lists of checkboxes and menus.

    - 'nocheck': no cross-checking against the valid values of the field will be
      done by the widget upon parsing the form.
    """

    class_ = 'multiple'

    def __init__(self, name, values,
                 label=None, default=[], notnull=None, nocheck=None):
        Field.__init__(self, name, label, default, notnull)

        self.nocheck = nocheck
        atypes = (types.NoneType, types.ListType) + types.StringTypes
        assert default == [] or type(default) in atypes
        assert notnull in [None, True, False]

        self.setvalues(values)

    def setvalues(self, values):
        normvalues = []
        self.valuesset = set()
        if type(values) is types.ListType:
            for el in values:
                if type(el) == types.IntType:
                    el = str(el)
                if type(el) in types.StringTypes:
                    normvalues.append( (el, el) )
                    self.valuesset.add(el)
                else:
                    assert type(el) is types.TupleType
                    assert len(el) == 2
                    normvalues.append(el)
                    self.valuesset.add(el[0])

        elif type(values) is types.TupleType:
            assert len(values) == 2
            normvalues.append(values)
            self.valuesset.add(values[0])
        
        elif type(values) in types.StringTypes:
            normvalues = [ (values, values) ]
            self.valuesset.add(values)
        else:
            raise RuntimeError("Incorrect type for values in '%s'." % name)

        self.values = []
        for k, v in normvalues:
            # Assert that the keys are simple strings and not unicode types.
            # See convert_value_for_multiple for explanations.
            if not isinstance(k, types.StringType):
                raise SystemExit("Internal error: key '%s' is not a str." % k)

            # Decode values to Unicode.
            if isinstance(v, str):
                v = v.decode(_dec_encoding)
            self.values.append( (k, v) )

    def convert_value_for_multiple(self, value):
        """
        Convert the value to the appropriate type for multiple fields.

        Note: we restrict the values here not to be Unicode strings
        because of the way we often stored them using SQLObject which does
        causes a problem with EnumCol when mixing unicode and str objects
        (see _SO_update call to join()).
        """
        return value.encode('utf-8')

    def prepare_value(self, value):
        if isinstance(value, _strtype):
            if value not in self.valuesset:
                raise ValueError(
                    "'%s' is not in map for widget '%s'." % (value, self.name))
        elif type(value) is types.ListType:
            for v in value:
                if not isinstance(v, str):
                    raise ValueError
                if v not in self.valuesset:
                    raise ValueError
        return Field.prepare_value(self, value)


#-------------------------------------------------------------------------------
#
class RadioField(MultipleField):
    """
    A single choice among many.

    (This is represented as radio buttons.)
    """

    class_ = 'radio'

    def __init__(self, name, values,
                 label=None, default=[], notnull=None, nocheck=None, **kw):

        MultipleField.__init__(self, name, values,
                               label, default, notnull, nocheck)
        assert default == [] or type(default) in types.StringTypes
        assert notnull in [None, True, False]

        # use by renderers (optionally)
        self.minitable = kw.get('minitable', None)
        assert self.minitable in [None, 'vertical', 'horizontal']

    def parse(self, value):
        if not isinstance(value, _strtype):
            raise ValueError
        newvalue = self.convert_value_for_multiple(value)
        if not self.nocheck and newvalue not in self.valuesset:
            raise ValueError
        return newvalue

    def prepare_value(self, value):
        # always be prepared to accept an unspecified value for a radio button
        # field
        if value is None:
            return value
        return MultipleField.prepare_value(self, value)

#-------------------------------------------------------------------------------
#
class ListField(MultipleField):
    """
    Zero or many choices among many.

    (This is represented as a list of checkboxes.)
    """

    class_ = 'list'

    def __init__(self, name, values,
                 label=None, default=[], notnull=None, nocheck=None, **kw):

        MultipleField.__init__(self, name, values,
                               label, default, notnull, nocheck)
        assert default == [] or type(default) in types.StringTypes
        assert notnull in [None, True, False]

        # use by renderers (optionally)
        self.minitable = kw.get('minitable', None)
        assert self.minitable in [None, 'vertical', 'horizontal']

    def parse(self, value):
        if isinstance(value, _strtype):
            if not self.nocheck and value not in self.valuesset:
                raise ValueError
            value = self.convert_value_for_multiple(value)
            return [value]

        elif type(value) is types.ListType:
            newvalues = []
            for v in value:
                if not isinstance(v, _strtype):
                    raise ValueError
                if not self.nocheck and v not in self.valuesset:
                    raise ValueError
                newvalues.append(self.convert_value_for_multiple(v))
            return newvalues

#-------------------------------------------------------------------------------
#
class MenuField(RadioField, ListField):
    """
    Menu field, which can be used to choose a single item, or zero or many
    items.
    """

    class_ = 'menu'

    def __init__(self, name, values,
                 label=None, default=[], notnull=None, nocheck=None,
                 multiple=False, size=NoDef):

        MultipleField.__init__(self, name, values,
                               label, default, notnull, nocheck)
        self.multiple = multiple

        # Set size to 1 if a single choice is requested.  Otherwise set it to
        # something larger than one, so that we get a listbox from which to
        # select stuff.
        if size is NoDef:
            if multiple:
                self.size = min(len(values), 5)
            else:
                self.size = 1

    def parse(self, value):
        if self.multiple:
            return ListField.parse(self, value)
        else:
            return RadioField.parse(self, value)

#-------------------------------------------------------------------------------
#
class DateField(Field):
    """
    Verify that the field contains a date in a supported format. The
    return value is a Date instance.
    """

    class_ = 'date'

    dre = re.compile('(\d\d\d\d)-(\d\d)-(\d\d)')

    def parse(self, value):
        if not isinstance(value, _strtype):
            raise ValueError
        mo = self.dre.match(value)
        if not mo:
            raise ValueError
        return datetime.date(*map(int, mo.groups()))

#-------------------------------------------------------------------------------
#
class ActiveDateField(DateField):
    """
    A javascript-based date field.
    """

    class_ = 'date active'

    # Public data used for adding the script reference to the head.
    filename = 'calendarDateInput.js'
    notice = """
    Jason's Date Input Calendar- By Jason Moon http://www.jasonmoon.net/
    Script featured on and available at http://www.dynamicdrive.com
    Keep this notice intact for use.
    """

    dre = re.compile('(\d\d\d\d)(\d\d)(\d\d)')

    def __init__(self, name,
                 label=None, default=None, notnull=None):
        Field.__init__(self, name, label, default, notnull)

        # This verification is required for the JS calendar.
        assert re.match('^[a-zA-Z_]+$', name)




#-------------------------------------------------------------------------------
#
class FileUploadField(Field):
    """
    Verify that the field is a file upload field. The returned value is
    a FileUpload instance.
    """

    class_ = 'file'

    def __init__(self, name,
                 label=None, default=None, notnull=None, 
                 accept=None):
        Field.__init__(self, name, label, default, notnull)
        self.accept = accept

    def parse(self, value):
        # Note: to avoid the dependency on the caller, we only make sure that he
        # creates a class named 'FileUpload' to store the file-like object that
        # will allow reading the uploaded file.
        # if not isinstance(value, FileUpload):
        # That's why we only check 'by name' here.
        #
        # Note2: we need to accept string types too, since from the mechanize
        # encoding that's what we seem to get.
        if type(value) in types.StringTypes:
            return value
        elif type(value) == types.InstanceType and \
                 value.__class__.__name__ == 'FileUpload':
            return value
        raise ValueError


#-------------------------------------------------------------------------------
#
def handle_upload(arg):
    """
    Handles a file uploadb by wrapping either the string or the file object in a
    file object readied for reading.
    """
    if isinstance(arg, str):
        # we got data as a string, wrap around file-like object
        rfile = StringIO(arg)
    else:
        if arg is None or arg.file is None:
            raise KeyError

        assert arg.__class__.__name__ == 'FileUpload'

        # open data and check if empty
        arg.file.seek(0, 2) # end
        size = arg.file.tell()
        if size == 0:
            raise KeyError # empty file

        # success, rewind
        arg.file.seek(0)
        rfile = arg

    return rfile


#===============================================================================
# FORM
#=====

#-------------------------------------------------------------------------------
#
class FormError(Exception):
    """
    Exception to indicate that a form was entered incompletely or incorrectly.
    Either 'illegal' or 'required' are set to the erroneous fields.

    - 'illegal' indicates a parsing error.
    - 'required' indicates a field that should have been there but was not.

    """

    def __init__(self, illegal_fields=[], required_fields=[], args=[]):
        Exception.__init__(self, 'Form Error')
        self.illegal = illegal_fields
        self.required = required_fields
        self.args = args
        assert self.illegal or self.required

    def __str__(self):
        o = []
        if self.illegal:
            o.append('Illegal values for fields: %s.' % \
                     ', '.join(map(lambda x: x.name, self.illegal)))
        if self.required:
            o.append('Required values for fields: %s.' % \
                     ', '.join(map(lambda x: x.name, self.required)))
        return ' '.join(o)

    def parsed_args(self):
        return self.args

    def errfields(self):
        """
        Returns a list of erroneous fields.
        """
        return self.illegal + self.required

    def errnames(self):
        """
        Returns a list of erroneous field names.
        """
        return [x.name for x in self.illegal + self.required]

    def errlabels(self):
        """
        Returns a printable list of erroneous field labels, comma-separated.
        """
        return filter(None,
                      map(lambda x: x.label, self.illegal + self.required))

    def formerrors(self):
        """
        Retuns a dict suitable for setting as form errors.
        """
        d = {}
        for f in self.illegal:
            d[f.name] = _('Illegal value.')
        for f in self.required:
            d[f.name] = _('Required value.')
        return d


#-------------------------------------------------------------------------------
#
class FormUniquenessError(Exception):
    """Exception that indicates that fields were added with names that are not
    unique."""


#-------------------------------------------------------------------------------
#
class Form:
    """
    A form consists of a number of input fields and output variables. The
    input fields are converted to the output variables using the parse()
    function.

    When a field is added using addField(), it becomes an input field and
    an output variable by default. The Form.parse() method uses
    Field.parse() function to convert from input (mod_python types) to
    the output format (Python types).

    By overriding the parse() method, an arbitrary (input field -> output
    variable) mapping can be constructed.

    Each form must have a name and an action associated with it.

    Forms can be rendered by specifying an appropriate renderer adapter.

    The 'submit' keyword argument can be a string or a list of (name, value)
    pairs, to indicate multiple submit buttons.
    """

    __def_action = None
    __def_submit = 'Submit'
    __def_method = 'POST'
    __def_encoding = 'UTF-8'

    def __init__(self, name, *fields, **kwds):
        """
        Form creation.  You can specify 'action', 'submit' (button name) and
        'method' (GET or POST) here.
        """
        assert isinstance(name, str)
        self.name = name
        self.action = kwds.get('action', self.__def_action)
        self.submit = kwds.get('submit', self.__def_submit)
        self.method = kwds.get('method', self.__def_method)
        self.encoding = kwds.get('encoding', self.__def_encoding)
        assert self.name and self.submit
        assert type(self.submit) in \
               types.StringTypes + (types.ListType, types.TupleType)

        self.m_fields = []
        self.m_fieldmap = {}

        # Unroll nested lists of fields.
        def unroll_fields(forl):
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
            self.addField(field)

    def __getitem__(self, name):
        """
        Get a field by name.
        """
        return self.m_fieldmap[name]

    def fields(self):
        """
        Return a list containing the form fields.
        """
        return self.m_fields

    def names(self):
        """
        Returns a list of the field names.
        """
        return [x.name for x in self.m_fields]

    def labels(self, fieldnames=None):
        """
        Returns a list of the labels of the fields.
        """
        if fieldnames is not None:
            fields = [self.m_fieldmap[x] for x in fieldnames]
        else:
            fields = self.m_fields
        return [x.label for x in fields]

    def fetchnames(self, obj, exceptions=[]):
        """
        Fetches the fieldname attributes from the given object and returns a
        mapping with those values.  This can be useful if 'obj' is an ORM object
        with dynamic values.
        """
        values = {}
        for field in self.m_fields:
            if field.name in exceptions:
                continue
            try:
                values[field.name] = getattr(obj, field.name)
            except AttributeError:
                pass
        return values

    def addField(self, field):
        """
        Add a field to the form. The field argument must be a Field instance.
        """
        if not isinstance(field, Field):
            raise TypeError, 'Expecting a Field instance.'
        if field.name in self.m_fieldmap:
            raise FormUniquenessError
        self.m_fields.append(field)
        self.m_fieldmap[field.name] = field

    def parse(self, args):
        """
        Parse the form, raising a FormError on error.  This is also the
        validation function.  Note that this extracts ONLY the fields of args
        for which there are corresponding fields.

        Note: if there is an error, the FormError contains a copy of the
        arguments that were succesfully parsed.

        If an argument is not provided for a widget that is present in the form,
        either the default value of the widge is set or None, to indicate the
        absence of the value.  A value for all the widget names is guaranteed to
        be present in the returned array, with values of None for those
        arguments that were not present.

        FIXME: we need to improve this method by allowing to specify a list of
        the arguments to process and which to ignore as well.  This would
        typically be done by via the FormParser object initialization.
        """
        parsed_args = {}
        illegal = []
        required = []
        for fi in self.m_fields:
            if args.get(fi.name):
                try:
                    arge = args[fi.name]
                    if self.encoding and not isinstance(fi, FileUploadField):
                        if isinstance(arge, str):
                            try:
                                arge = arge.decode(self.encoding)
                            except UnicodeDecodeError, e:
                                # broken client, not much we can do.
                                raise RuntimeError("Incorrectly encoded input.")

                        if isinstance(arge, types.ListType):
                            arge_out = []
                            for a in arge:
                                try:
                                    arge_out.append(a.decode(self.encoding))
                                except UnicodeDecodeError, e:
                                    # broken client, not much we can do.
                                    raise RuntimeError(
                                        "Incorrectly encoded input.")
                            arge = arge_out

                    value = fi.parse(arge)
                    parsed_args[fi.name] = value
                    
                    # check for validators
                    if fi.validators:
                        for val in fi.validators:
                            val.validate(value)

                except ValueError:
                    illegal.append(fi)

            elif fi.notnull:
                required.append(fi)

            else:
                parsed_args[fi.name] = fi.default

        if illegal or required:
            pargs_copy = dict(parsed_args)
            for field in illegal:
                if field.name in pargs_copy:
                    del pargs_copy[field.name]
            raise FormError(illegal, required, pargs_copy)
        else:
            return parsed_args

    def parse_submit(self, args):
        """
        Parse the multiple submit buttons if necessary.
        Returns the string of the chosen button, or None, if not relevant.
        """
        if len(self.submit) <= 1:
            return None
        else:
            for n in self.submit:
                if isinstance(n, str):
                    pass
                elif isinstance(n, tuple):
                    n = n[0]
                else:
                    raise RuntimeError("Internal Error.")
                if n in args:
                    return n
                    # Note: we don't check if there are more than one, we will
                    # just take the first one. If someone is trying to hack by
                    # fiddling with the submit values, it will be just as if the
                    # first one is chosen.
            return None


#===============================================================================
# RENDERER
#=========

#-------------------------------------------------------------------------------
#
def clsiter(obj):
    """Iterator that works its way up the class hierarchy of the given object."""

    clsstk = [obj.__class__]

    while clsstk:
        cls = clsstk.pop()
        yield cls
        clsstk.extend(cls.__bases__)

#-------------------------------------------------------------------------------
#
class BaseRenderer:
    """
    Base class for renderer visitors.
    """

    def dispatch(self, func, field, *args):
        """
        Dispatch to function with base 'func' on type 'field.  Your derived
        class must have methods func_<type>.  A search is made up the
        inheritance tree, and if an appropriate method for the given type is not
        found, method 'func_default' is called.
        """

        for cls in clsiter(field):
            mname = '%s_%s' % (func, cls.__name__)
            if hasattr(self, mname):
                method = getattr(self, mname)
                return method(field, *args)
        else:
            raise RuntimeError("No method to handle field '%s'." % field)

    def renderhidden(self, field, value, tr):
        """
        Override this method to render the hidden fields.
        """
        raise NotImplementedError

    def renderfield(self, field, values, tr, noempty=False):
        """
        Render a single field of the form.
        """
        if field.ishidden():
            if noempty:
                return None
            try:
                value = values[field.name]
            except (KeyError, TypeError):
                raise RuntimeError(
                    "Hidden field '%s' has no value." % field.name)
        else:
            if values:
                value = values.get(field.name, field.default)
            else:
                value = field.default

        if noempty:
            if value is None or value == field.default:
                return None

        # Prepare value for rendering
        pvalue = field.prepare_value(value)

        # FIXME: the following needs to be defined more clearly at some point,
        # the possible types for all the possible widgets.  We will need to
        # write a lot of automated tests to see how this behaves, and right now
        # this code is coupled too tightly with the form renderer.
        
        # Convert pod to a string, so we can specify other types for default
        # value.
        if pvalue and type(pvalue) is not types.ListType:
            if pvalue is True:
                pvalue = '1'
            elif pvalue is False:
                pvalue = '0'
            elif pvalue is None:
                pvalue = ''
            elif type(pvalue) is datetime.date:
                pass
            else:
                # Not sure we should do this, see date above.
                if not isinstance(pvalue, types.StringTypes):
                    pvalue = unicode(pvalue)

        if field.label is None:
            output = self.renderhidden(field, pvalue, tr)
        else:
            output = self.dispatch('render', field, pvalue, tr)
        return output

    def renderfields(self, form, values, tr, noempty=False, fields=None):
        """
        Generator for rendering fields.
        Derived classes should use this.

        - 'noempty': does not render fields that are either empty or set to
          defaults.
        """
        for field in form.fields():
            # if restricting to specific fields, skip the fields that are not in
            # the list.
            if fields and field.name not in fields:
                continue
            output = self.renderfield(field, values, tr, noempty)
            if output is None:
                continue
            yield output, field


#-------------------------------------------------------------------------------
#
def tr_noop(s):
    "Noop translation service."
    return s

#-------------------------------------------------------------------------------
#
class SimpleRenderer(BaseRenderer):

    """Test renderer that simply outputs HTML forms directly.  You could write
    your own renderer that builds a tree of XML nodes and then flattens that to
    a file instead.  This would be done outside of this library to avoid the
    extra dependency.

    Note that you could also write a renderer to display data in the form of
    tables, without the input forms.  Such a renderer could be used to display
    data without editing capabilities (with an [Edit] button/link perhaps?).
    """

    def render(self, form, values=None, errors=None, tr=None):
        """Render the form, filling in the values that are present with the
        contents of the 'values' mapping (for example, as can be extracted with
        the cgi module)."""

        if tr is None:
            tr = tr_noop

        f = StringIO.StringIO()

        print >> f, '<form id="%(name)s" name="%(name)s" ' % form.__dict__
        print >> f, '      action="%(action)s" method="%(method)s">' % \
              form.__dict__
        print >> f, '  <table>'

        hidden = ''
        for output, field in self.renderfields(form, values, tr):
            if field.label is None:
                hidden += output # save for later
            else:
                f.write(output)

        print >> f, '  </table>'
        print >> f, hidden
        if isinstance(form.submit, str):
            print >> f, '  <input type="submit" value="%s" />' % tr(form.submit)
        else:
            for name, value in form.submit:
                print >> f, '  <input type="submit" name="%s" value="%s" />' % \
                      (name, tr(value))

        print >> f, '</form>'
        return f.getvalue()

    __fieldfmt = "  <tr>\n    <td>%(label)s</td>\n" \
                 "    <td>%(inputs)s</td>\n  </tr>\n"
    __fieldfmt_hidden = "%(inputs)s\n"

    def renderhidden(self, field, value, tr):
        if value is None: value = ''
        elif value is True: value = '1'
        elif value is False: value = '0'

        if isinstance(value, str):
            inpu = '<input name="%s" type="hidden" value="%s" />\n' % \
                   (field.name, value)
        elif type(value) is types.ListType:
            inpu = ''
            for val in value:
                inpu += '<input name="%s" type="hidden" value="%s" />\n' % \
                        (field.name, val)
        else:
            raise RuntimeError

        return inpu

    def render_Field(self, field, value, tr, type_='text', checked=NoDef):
        label = tr(field.label)

        vstr = ''
        if value:
            vstr += 'value="%s" ' % value
        if checked is not NoDef and checked:
            vstr += 'checked="checked"'

        inpu = '<input name="%s" type="%s" %s/>' % (field.name, type_, vstr)

        return self.__fieldfmt % {'label': label, 'inputs': inpu}

    def render_StringField(self, field, value, tr):
        return self.render_Field(field, value, tr, 'text')

    def render_PasswordField(self, field, value, tr):
        return self.render_Field(field, value, tr, 'password')

    def render_TextAreaField(self, field, value, tr):
        label = tr(field.label)

        astr = []
        if field.rows:
            astr += ['rows="%s"' % field.rows]
        if field.cols:
            astr += ['cols="%s"' % field.cols]

        inpu = '<textarea name="%s" %s>%s</textarea>' % \
               (field.name, ' '.join(astr), value or '')

        return self.__fieldfmt % {'label': label, 'inputs': inpu}

    def render_IntField(self, field, value, tr):
        return self.render_Field(field, value, tr, 'text')

    def render_FloatField(self, field, value, tr):
        return self.render_Field(field, value, tr, 'text')

    def render_BoolField(self, field, value, tr):
        return self.render_Field(field, '1', tr, 'checkbox', checked=value)

    def render_MultipleField(self, field, value, tr, type_):
        label = tr(field.label)

        inpu = '\n'
        for fvalue, flabel in field.values:
            vstr = ''
            if type(value) is types.ListType:
                if fvalue in value:
                    vstr += 'checked="checked" '
            elif fvalue == value:
                vstr += 'checked="checked" '
            inpu += ('<input name="%s" value="%s" type="%s" %s>%s' + \
                     '</input><br/>\n') % \
                     (field.name, fvalue, type_, vstr, flabel)

        return self.__fieldfmt % {'label': label, 'inputs': inpu}

    def render_RadioField(self, field, value, tr):
        return self.render_MultipleField(field, value, tr, 'radio')

    def render_ListField(self, field, value, tr):
        return self.render_MultipleField(field, value, tr, 'checkbox')

    def render_MenuField(self, field, value, tr):
        label = tr(field.label)

        mulstr = field.multiple and 'multiple="1"' or ''
        mulstr += ' size="%d"' % (field.size or 1)
        inpu = '\n<select name="%s" %s>\n' % (field.name, mulstr)
        for fvalue, flabel in field.values:
            selstr = ''
            if type(value) is types.ListType:
                if fvalue in value:
                    selstr = 'selected="selected"'
            elif fvalue == value:
                selstr = 'selected="selected"'

            inpu += '  <option value="%s" %s>%s</option>\n' % \
                    (fvalue, selstr, flabel)

        inpu += '\n</select>'

        return self.__fieldfmt % {'label': label, 'inputs': inpu}

    def render_DateField(self, field, value, tr):
        return self.render_Field(field, value, tr, 'text')

    def render_FileUploadField(self, field, value, tr):
        return self.render_Field(field, value, tr, 'file')



#===============================================================================
# TEST
#===============================================================================

# Note: minimal tests, this library has actually been used during development
# and therefore much more tested than this.  I should really complete the tests
# here at some point.

import unittest, sys, os

#-------------------------------------------------------------------------------
#
lastwrite = None

def getcodediff(nframes):
    """
    Returns the difference in code between the given filename and lineno and the
    last one encountered.
    """
    global lastwrite


    fr = sys._getframe(1 + nframes)
    fn = fr.f_code.co_filename
    func = fr.f_code.co_name
    lno = fr.f_lineno

    if lastwrite is None:
        lastwrite = (fn, func, lno)
        return None, None
    else:
        oldfn, oldfunc, oldlno = lastwrite
        lastwrite = (fn, func, lno)

        if fn != oldfn or func != oldfunc:
            # return until the beginning of the calling function
            oldlno = fr.f_code.co_firstlineno

        text = open(fn, 'r').read()
        lines = [oldlno, lno]
        lines.sort()

        filelines = text.splitlines()
        lpairs = [(x, filelines[x-1]) for x in xrange(*lines)]
        return func, os.linesep.join('%d  %s' % x for x in lpairs)

#-------------------------------------------------------------------------------
#
def _write(output):
    "Write output to test file."

    print '/------------------------------'
    funcname, code = getcodediff(1)
    print funcname, ':'
    print code
    print '\------------------------------'

    print output

    import os, tempfile, webbrowser
    fd, name = tempfile.mkstemp(suffix='.html')
    os.write(fd, output)
    os.close(fd)
    webbrowser.open_new(name)

#-------------------------------------------------------------------------------
#
class TestsCreate(unittest.TestCase):

    def test_uniqueness(self):
        try:
            Form('form-1',
                 StringField('rachel'),
                 StringField('rachel'))
            raise RuntimeError
        except FormUniquenessError:
            pass

#-------------------------------------------------------------------------------
#
class TestsRender(unittest.TestCase):

    renderer = SimpleRenderer()

    def test_render(self):

        form = Form('form-1',
                    StringField('bli2')
                    )
        self.assertRaises(RuntimeError, self.renderer.render, form)

        form = Form(
            'form-1',
            StringField('lang', "Language"),
            PasswordField('passwd', "Password"),
            StringField('bli', "Bli Field", default='bli'),
            StringField('bli2', "Other Field", default='bli'),
            BoolField('option', "Some Option", default=True),
            IntField('someint', default='hiddenval'),
            ListField('blaah', {'o1': "Some Option",
                                   'o2': "Other Option"}, default=['o2']),
            submit="Set Language"
            )

        values = {'bli': 'Bliperdooblip!',
                  'lang': None,
                  'someint': 17}
        errors = {'bli': "Please enter something better than this."}

        o = self.renderer.render(form, values, errors)
        _write(o)

    def test_enums(self):

        choices = [ ('fr', "Francais"),
                    ('en', "English"),
                    ('jp', "Nihongo"),
                    ('es', "Espanol") ]
        form = Form(
            'form-1',
            RadioField('lang', choices, "Language"),
            submit="Set Language"
            )
        self.renderer.render(form)

        form = Form(
            'form-1',
            ListField('lang', choices, "Language"),
            submit="Set Language"
            )
        self.renderer.render(form)

        form = Form(
            'form-1',
            MenuField('lang', choices, "Language", size=1),
            submit="Set Language"
            )
        self.renderer.render(form)

        choices = ['fr', 'en', 'es', 'jp', 'pt']
        form = Form(
            'form-1',
            ListField('lang', choices, "Language", default=['en', 'jp']),
            submit="Set Language"
            )
        self.renderer.render(form)


    def test_file(self):

        form = Form(
            'form-1',
            FileUploadField('somefile', "File Upload"),
            submit="Upload file"
            )
        self.renderer.render(form)

    def test_hide_password(self):

        form = Form(
            'form-1',
            PasswordField('password', "The Password"),
            submit="Login"
            )

        t = self.renderer.render(form, values={'password': 'bigsecret'})
        assert re.search('bigsecret', t) == None

#-------------------------------------------------------------------------------
#
class TestsParse(unittest.TestCase):

    def test_simple(self):

        form = Form(
            'form-1',
            StringField('username', "Username", notnull=1),
            PasswordField('password', "Password", notnull=1),
            submit="Login"
            )

        self.assertRaises(FormError, form.parse, {})

        vals = {'username': 'blais'}
        self.assertRaises(FormError, form.parse, vals)

        vals = {'username': 'blais', 'password': 'bli'}
        form.parse(vals)

        vals = {'username': 'blais\ndsjdjs', 'password': 'bli'}
        self.assertRaises(FormError, form.parse, vals)


#-------------------------------------------------------------------------------
#
class TestFields(unittest.TestCase):

    renderer = SimpleRenderer()

    def test_string(self):
        class_ = StringField

        # visible form, valid
        form = Form( 'form-1',
                     class_('thetext', 'Some Text') )
        _write(self.renderer.render(form))

        vals = {'thetext': 'Bendito me diste la fe'}

        # parse
        form = Form( 'form-1',
                     class_('thetext', 'Some Text') )
        args = form.parse({})
        assert args['thetext'] == ''

        args = form.parse(vals)
        assert args['thetext'] == 'Bendito me diste la fe'

        # hidden form
        form = Form( 'form-1',
                     class_('thetext') )
        self.assertRaises(RuntimeError, self.renderer.render, form)

        _write(self.renderer.render(form, vals))

    def test_password(self):
        class_ = PasswordField

        # visible form, valid
        form = Form( 'form-1',
                     class_('passwd', 'Password') )
        _write(self.renderer.render(form))

        vals = {'passwd': 'secreto'}

        # parse
        form = Form( 'form-1',
                     class_('passwd', 'Password', default=17) )

        args = form.parse(vals)
        assert args['passwd'] == 'secreto'

        args = form.parse({})
        assert args['passwd'] == 17

        # hidden form
        form = Form( 'form-1',
                     class_('passwd') )
        _write(self.renderer.render(form, vals))

    def test_textarea(self):
        class_ = TextAreaField
        roman = "Ven ven ven!  Pa'que tu vea como es el tren..."

        # visible form, valid
        form = Form( 'form-1',
                     class_('roman', 'Un Roman') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('roman', 'Un Roman',
                                   roman, rows=50, cols=100) )
        _write(self.renderer.render(form))


        # parse
        vals = {'roman': roman}
        args = form.parse(vals)

        # hidden form
        form = Form( 'form-1',
                     class_('roman') )
        _write(self.renderer.render(form, vals))

    def test_int(self):
        class_ = IntField
        # visible form, valid
        form = Form( 'form-1',
                     class_('winning', 'Winning Number') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('winning', 'Winning Number', 42) )
        _write(self.renderer.render(form))

        # parse
        vals = {'winning': '17'}
        args = form.parse(vals)

        self.assertRaises(FormError, form.parse, {'winning': 'fuera de liga!'})

        # hidden form
        form = Form( 'form-1',
                     class_('winning') )
        _write(self.renderer.render(form, vals))

    def test_float(self):
        class_ = FloatField
        # visible form, valid
        form = Form( 'form-1',
                     class_('winning', 'Winning Number') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('winning', 'Winning Number', 42.17) )
        _write(self.renderer.render(form))
        return

        # parse
        vals = {'winning': '34.32'}
        args = form.parse(vals)

        self.assertRaises(FormError, form.parse, {'winning': 'vive tu vida!'})

        # hidden form
        form = Form( 'form-1',
                     class_('winning') )
        _write(self.renderer.render(form, vals))

    def test_bool(self):
        class_ = BoolField
        # visible form, valid
        form = Form( 'form-1',
                     class_('wanting', 'She Wanting?') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('wanting', 'She Wanting?', False) )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('wanting', 'She Wanting?', True) )
        _write(self.renderer.render(form))

        # parse
        vals = {'wanting': '0'}
        args = form.parse(vals)

        # hidden form
        vals = {'wanting': False}
        form = Form( 'form-1',
                     class_('wanting') )
        _write(self.renderer.render(form, vals))

        vals = {'wanting': True}
        form = Form( 'form-1',
                     class_('wanting') )
        _write(self.renderer.render(form, vals))


    def test_radio(self):
        class_ = RadioField
        choices = [ ('ha', 'La Habana'),
                    ('ci', 'Cienfuegos'),
                    ('sa', 'Santiago') ]

        # visible form, valid
        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices', 'ci') )
        _write(self.renderer.render(form))

        # parse
        vals = {'ciudad': ['ci', 'ha']}
        self.assertRaises(FormError, form.parse, vals)

        vals = {'ciudad': 'ci'}
        args = form.parse(vals)

        # hidden form
        form = Form( 'form-1',
                     class_('ciudad', choices) )
        _write(self.renderer.render(form, vals))

    def test_list(self):
        class_ = ListField
        choices = [ ('ha', 'La Habana'),
                    ('ci', 'Cienfuegos'),
                    ('sa', 'Santiago') ]

        # visible form, valid
        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices', 'ci') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices', default=['ha', 'sa']) )
        _write(self.renderer.render(form))

        # parse
        vals = {'ciudad': 'ci'}
        args = form.parse(vals)

        vals = {'ciudad': ['ci', 'ha']}
        args = form.parse(vals)

        vals = {'ciudad': ['ci', 'bi']}
        self.assertRaises(FormError, form.parse, vals)

        # hidden form
        form = Form( 'form-1',
                     class_('ciudad', choices) )
        self.assertRaises(ValueError, self.renderer.render, form, vals)

        vals = {'ciudad': ['ci', 'ha']}
        form = Form( 'form-1',
                     class_('ciudad', choices) )
        _write(self.renderer.render(form, vals))

    def test_menu(self):
        class_ = MenuField

        choices = [ ('ha', 'La Habana'),
                    ('ci', 'Cienfuegos'),
                    ('sa', 'Santiago') ]

        # visible form, valid
        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices') )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices', multiple=1) )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices', multiple=1,
                            default=['ci', 'sa']) )
        _write(self.renderer.render(form))

        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices', multiple=1,
                            default='ha') )
        _write(self.renderer.render(form))

        # parse
        form = Form( 'form-1',
                     class_('ciudad', choices, 'Choices', multiple=1,
                            default='ci', notnull=1) )
        self.assertRaises(FormError, form.parse, {})

        vals = {'ciudad': ['ci', 'ha']}
        args = form.parse(vals)

        vals = {'ciudad': ['ci', 'bi']}
        self.assertRaises(FormError, form.parse, vals)

        # hidden form
        form = Form( 'form-1',
                     class_('ciudad', choices) )
        self.assertRaises(ValueError, self.renderer.render, form, vals)

        vals = {'ciudad': ['ci', 'ha']}
        form = Form( 'form-1',
                     class_('ciudad', choices) )
        _write(self.renderer.render(form, vals))


    def test_date(self):
        class_ = DateField

        # visible form, valid
        form = Form( 'form-1',
                     class_('fired', 'Fired On') )
        _write(self.renderer.render(form))

        # parse
        vals = {'fired': 'illegal date'}
        self.assertRaises(FormError, form.parse, vals)

        vals = {'fired': '2004-05-06'}
        args = form.parse(vals)

        # hidden form
        form = Form( 'form-1',
                     class_('fired') )
        _write(self.renderer.render(form, vals))

    def test_file(self):
        class_ = FileUploadField

## FIXME todo, write more tests.


#-------------------------------------------------------------------------------
#
def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestFields('test_radio'))
    return suite

#-------------------------------------------------------------------------------
#
def all():
    return unittest.makeSuite(TestFields)

#-------------------------------------------------------------------------------
#
if __name__ == '__main__':
    unittest.main()

