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
File Upload Fields
"""

# stdlib imports
import StringIO
from types import NoneType, InstanceType

# atocha imports
from atocha import AtochaError, AtochaInternalError
from atocha.field import Field, FieldError, OptRequired
from atocha.messages import msg_registry
from bools import BoolField

__all__ = ('FileUploadField', 'SetFileField', 'FileUpload',)



class FileUpload:
    """
    Adapter class for the mod_python Field class that implements the file
    interface.  This slightly changes the semantics of mod_python's Field
    class. It imports the file operations from the temporary file to the current
    class so it can be used as a file.
    """

    def __init__(self, obj, filename=None):
        self.obj = obj
        """The object that contains a 'file' member, from which the contents of
        the upload can be read."""

        self.filename = filename
        """The name of the file that is uploaded, if available."""

    def __nonzero__(self):
        return True # To be able to test with parser['filefield'].

    def __getattr__(self, name):
        """
        Aggregate file methods into the current object.
        """
        if hasattr(self.obj.file, name):
            attr = getattr(self.obj.file, name)
            if callable(attr):
                return attr
        return getattr(self.obj, name)



class FileUploadField(Field, OptRequired):
    """
    A file being sent by the client.  The returned value is an instance of the
    FileUpload class.

    There are lots of details about file upload mechanics at
    http://www.cs.tut.fi/~jkorpela/forms/file.html

    To peruse the results of a file upload object, you will be given access to a
    FileUpload class, on which you will be able to read() the contents or access
    the .filename attribute, e.g. ::

       binary_image = parser['photo'].read()
       client_filename = parser['photo'].filename

    Depending on the web framework using this, it might not be possible to get
    access to the filename, this depends on your backend.  In any case, the
    filename that comes from the client side is not very useful anyway, apart
    maybe to initialize a file upload field on query, and even then, most
    browsers do not allow this to happen (it could be a security problem).

    Note that the parser's getvalue() method will cull the results from
    FileUpload fields, because of the way these values are usually meant to be
    used--that is, as form data to be pickled or passed around.  You are
    supposed to handle file upload data manually.

    Observer that this field type is treated a little bit specially in the
    re-render loop: its values are removed automatically from the form-data (see
    FormParser) and the display renderers ignore and do not render them.
    """

    types_data = (NoneType, FileUpload,)
    types_parse = (NoneType, InstanceType, unicode,)
    types_render = (unicode,)
    css_class = 'file'

    attributes_declare = (
        ('filtpat', 'str',
         """Filter string to initialize the browser dialog on the client-side
         with. This corresponds to the 'accept' attribute of the corresponding
         HTML input field."""),
        )
         
    def __init__(self, name, label=None, **attribs):
        FileUploadField.validate_attributes(attribs)

        self.filtpat = attribs.pop('filtpat', None)

        OptRequired.__init__(self, attribs)
        Field.__init__(self, name, label, attribs)

    def parse_value(self, pvalue):
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

        # Check for not submitted.
        if pvalue is None:
            dvalue = None

        # Check for strings.
        elif isinstance(pvalue, unicode):
            # We got data as a string, wrap around file-like object.
            #
            # Note: we need to accept string types, since from the mechanize
            # library submit, that allows us to write tests, that's what we seem
            # to get.
            if pvalue:
                dvalue = StringIO.StringIO(pvalue)
            else:
                dvalue = None

        elif isinstance(pvalue, InstanceType):
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
                size = pvalue.file.tell()
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
            raise AtochaInternalError(
                "Internal error: type for file parsing unknown.")

        # Check the required value, this forces at least one choice to be
        # present. We don't delegate to the base class on purpose, this is a
        # special case.
        if self.required and pvalue is None:
            # We indicate an error mentioning that this field was required.
            raise FieldError(msg_registry['error-required-value'])

        return dvalue

    def render_value(self, dvalue):
        # Never render anything in there, it's not really used by browsers
        # anyway (at least not without a warning, when it is, e.g. Opera).
        return u''

    def display_value(self, dvalue):
        # Nothing to display from this, it's a file, you'll have to do something
        # special.
        if dvalue is not None:
            raise AtochaError("Error: attempting to display a file upload.")
        return u''



class SetFileField(FileUploadField):
    """
    A file being set or reset by the client.  The returned value is an instance
    of the FileUpload class.  This field provides a way that a client can submit
    a new file or remove an existing file from the server.  If the client enters
    a value to be sent, the uploaded file is meant to replace the existing one,
    and if a special 'Remove' checkbox is checked, it sends a message to remove
    the file instead.

    See FileUploadField for more details on the basic mechanisc of this field.

    There are lots of details about file upload mechanics at
    http://www.cs.tut.fi/~jkorpela/forms/file.html

    To peruse the results of this field, you need to observe the returned value,
    which can be one of:

    - None: the field was not filled/not submitted;
    - False: the server file is to be removed;
    - instance of FileUpload: the file is to be replaced.

    Note: it would be nice to be able to disable the file widget when the reset
    button is enabled. We need to write a little bit of JavaScript to do that.
    """

    types_data = (NoneType, FileUpload, bool)
    types_parse = (NoneType, dict)
    css_class = 'setfile'

    __resetext = '_reset'

    attributes_declare = (
        ('remlabel', 'str',
         """String to be used as the label for the 'reset' checkbox.  This
         should be a string that will only get translated at the moment of
         rendering."""),
        )

    def __init__(self, name, label=None, **attribs):
        SetFileField.validate_attributes(attribs)

        self.remlabel = attribs.pop('remlabel', None)
        if self.remlabel is None:
            self.remlabel = msg_registry.get_notrans('setfile-reset')
        assert isinstance(self.remlabel, str)

        FileUploadField.__init__(self, name, label, **attribs)

        # We use two variable names in this field: the basic name for the file
        # upload, and another name for the checkbox.
        self.varnames.append(self.name + self.__resetext)

    def parse_value(self, pvalue):
        pvfile, pvreset = [pvalue[self.varnames[x]] for x in 0, 1]
        assert isinstance(pvfile, FileUploadField.types_parse)
        assert isinstance(pvreset, BoolField.types_parse)

        if pvreset is None or pvreset == u'':
            # If reset is not specified, parse as a file and return that.
            return FileUploadField.parse_value(self, pvfile)
        else:
            # The field is to be reset. Return False object.
            return False

