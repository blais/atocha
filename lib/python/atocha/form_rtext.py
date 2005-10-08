#!/usr/bin/env python
#
# $Id$
#

"""
Simple text-based form renderers.
"""

# stdlib imports.
import StringIO, codecs

# form imports.
from form_render import FormRenderer
from form_messages import msg_type


__all__ = ['TextFormRenderer']


#-------------------------------------------------------------------------------
#
class TextFormRenderer(FormRenderer):
    """
    Form renderer that outputs HTML text directly.

    See base class for full details.
    """

    # Default encoding for output.
    default_encoding = 'UTF-8'

    # CSS class for errors.
    css_errors = 'form-error'
    css_table = 'form-table'
    css_label = 'form-label'
    css_input = 'form-input'

    def __init__( self, *args, **kwds ):
        """
        Grab the encoding parameter on top of the basic form renderer
        construction parameters.
        """

        try:
            self.outenc = kwds['output_encoding']
            del kwds['output_encoding']
        except KeyError:
            self.outenc = self.default_encoding
        """Encoding for output strings produced by this renderer."""

        try:
            self.label_semicolon = kwds['labelsemi']
            del kwds['labelsemi']
        except KeyError:
            self.label_semicolon = False
        """Whether we automatically add a semicolon to the labels or not."""

        FormRenderer.__init__(self, *args, **kwds)


    def __create_buffer( self ):
        """
        Create the default file for output.
        """
        return codecs.EncodedFile(StringIO.StringIO(), self.outenc)


    def do_render( self, fields, action, submit ):
        form = self._form
        try:
            # File object that gets set as a side-effect.
            self.ofile = f = self.__create_buffer()

            # (Side-effect will add to the file.)
            self.do_render_container(action)

            # (Side-effect will add to the file.)
            self.do_render_table(fields)

            # Render submit buttons.
            self.do_render_submit(submit)

            # Close the form (the container rendering only outputs the header.
            print >> f, '</form>'
        finally:
            self.ofile = None

        return f.getvalue()


    def do_render_container( self, action ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self.__create_buffer()
        form = self._form

        assert action is not None

        print >> f, ('<form id="%s" name="%s" action="%s" method="%s"' %
                     (form.name, form.name, action, form.method))

        if self.ofile is None: return f.getvalue()


    def do_render_table( self, fields ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self.__create_buffer()

        print >> f, '<table class="%s">' % self.css_table
        hidden_rendered = []
        for field in fields:
            rendered = self._render_field(field)
            if field.ishidden():
                hidden_rendered.append(rendered)
            else:
                label = field.label and _(field.label) or ''
                if self.label_semicolon:
                    label += ':'
                print >> f, (('<tr><td class="%s">%s</td>\n'
                              '    <td class="%s">%s</td></tr>') %
                             (self.css_label, label, self.css_input, rendered))
        print >> f, '\n'.join(hidden_rendered)
        print >> f, '</table>'

        if self.ofile is None: return f.getvalue()


    def do_table( self, label=None, inputs=None ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self.__create_buffer()

        print >> f, '<table>'
        for field in fields:
            label = label and _(label) or ''
            if self.label_semicolon:
                label += ':'
            print >> f, (('<tr><td class="%s">%s</td>\n'
                          '    <td class="%s">%s</td></tr>') %
                         (self.css_label, label, self.css_input, inputs))
        print >> f, '\n'.join(hidden_rendered)
        print >> f, '</table>'

        if self.ofile is None: return f.getvalue()


    def do_render_submit( self, submit ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self.__create_buffer()

        if isinstance(submit, msg_type):
            print >> f, ('<input type="submit" value="%s" />' %
                         _(submit).encode(self.outenc))
        else:
            assert isinstance(submit, (list, tuple))
            for value, name in submit:
                print >> f, \
                      ('<input type="submit" name="%s" value="%s" />' %
                       (name, _(value).encode(self.outenc)))

        if self.ofile is None: return f.getvalue()


    #---------------------------------------------------------------------------

    def renderHidden( self, field, rvalue ):
        inputs = []

        if isinstance(rvalue, str):
            inputs.append('<input name="%s" type="hidden" value="%s" />' %
                          (field.name, rvalue))
        elif isinstance(rvalue, (list, tuple)):
            for rval in rvalue:
                inputs.append('<input name="%s" type="hidden" value="%s" />' %
                              (field.name, rval))
        else:
            raise RuntimeError("Error: unexpected type '%s' for rendering." %
                               type(rvalue))

        return '\n'.join(inputs)


    def _geterror( self, error ):
        if error:
            return ('<span class="%s">%s</span><br/>' %
                    (self.css_errors, error))
        else:
            return ''

    def _simple( self, field, rvalue, error, required, htmltype ):
        """
        Render the simple field with the given parameters.
        """
        return (self._geterror(error) +
                '<input name="%s" type="%s" value="%s" class="%s" />' %
                (field.name, htmltype, rvalue or '', field.css_class))

    def renderStringField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'text')

    def renderTextAreaField( self, field, rvalue, error, required ):
        s = self._geterror(error)
        rowstr = field.rows and ' rows="%d"' % field.rows or ''
        colstr = field.cols and ' cols="%d"' % field.cols or ''
        return (self._geterror(error) +
                '<textarea name="%s" %s %s class="%s">%s</textarea>' %
                (field.name, rowstr, colstr, field.css_class, rvalue or ''))

        return self._simple(field, rvalue, error, required, 'text')

    def renderPasswordField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'text')

    def renderDateField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'text')

    def renderEmailField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'text')

    def renderURLField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'text')

    def renderIntField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'text')

    def renderFloatField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'text')

    def renderBoolField( self, field, rvalue, error, required ):
        return self._simple(field, rvalue, error, required, 'checkbox')

##  def render_MultipleField( self, field, rvalue, error, required ):
##  def render_Orientable:( self, field, rvalue, error, required ):
##  def render_OneChoiceField( self, field, rvalue, error, required ):
##  def renderRadioField( self, field, rvalue, error, required ):
##  def renderMenuField( self, field, rvalue, error, required ):
##  def render_ManyChoicesField( self, field, rvalue, error, required ):
##  def renderCheckboxesField( self, field, rvalue, error, required ):
##  def renderListboxField( self, field, rvalue, error, required ):
##  def renderJSDateField( self, field, rvalue, error, required ):
##  def renderFileUploadField( self, field, rvalue, error, required ):
##  def renderFileUpload( self, field, rvalue, error, required ):

# FIXME: support the required field.

## FIXME: complete this.






#
# # guarantees that we have that the value will be a bool.
#     def render_Field( self, field, value, type_='text', checked=NoDef ):
#         label = _(field.label)
#
#         vstr = ''
#         if value:
#             vstr += 'value="%s" ' % value
#         if checked is not NoDef and checked:
#             vstr += 'checked="checked"'
#
#         inpu = '<input name="%s" type="%s" %s/>' % (field.name, type_, vstr)
#
#         return self.__fieldfmt % {'label': label, 'inputs': inpu}
#
#     def render_StringField( self, field, value ):
#         return self.render_Field(field, value, 'text')
#
#     def render_PasswordField( self, field, value ):
#         return self.render_Field(field, value, 'password')
#
#     def render_TextAreaField( self, field, value ):
#         label = _(field.label)
#
#         astr = []
#         if field.rows:
#             astr += ['rows="%s"' % field.rows]
#         if field.cols:
#             astr += ['cols="%s"' % field.cols]
#
#         inpu = '<textarea name="%s" %s>%s</textarea>' % \
#                (field.name, ' '.join(astr), value or '')
#
#         return self.__fieldfmt % {'label': label, 'inputs': inpu}
#
#     def render_IntField( self, field, value ):
#         return self.render_Field(field, value, 'text')
#
#     def render_FloatField( self, field, value ):
#         return self.render_Field(field, value, 'text')
#
#     def render_BoolField( self, field, value ):
#         return self.render_Field(field, '1', 'checkbox', checked=value)
#
#     def render_MultipleField( self, field, value, type_ ):
#         label = _(field.label)
#
#         inpu = '\n'
#         for fvalue, flabel in field.values:
#             vstr = ''
#             if type(value) is types.ListType:
#                 if fvalue in value:
#                     vstr += 'checked="checked" '
#             elif fvalue == value:
#                 vstr += 'checked="checked" '
#             inpu += ('<input name="%s" value="%s" type="%s" %s>%s' + \
#                      '</input><br/>\n') % \
#                      (field.name, fvalue, type_, vstr, flabel)
#
#         return self.__fieldfmt % {'label': label, 'inputs': inpu}
#
#     def render_RadioField( self, field, value ):
#         return self.render_MultipleField(field, value, 'radio')
#
#     def render_ListField( self, field, value ):
#         return self.render_MultipleField(field, value, 'checkbox')
#
#     def render_MenuField( self, field, value ):
#         label = _(field.label)
#
#         mulstr = field.multiple and 'multiple="1"' or ''
#         mulstr += ' size="%d"' % (field.size or 1)
#         inpu = '\n<select name="%s" %s>\n' % (field.name, mulstr)
#         for fvalue, flabel in field.values:
#             selstr = ''
#             if type(value) is types.ListType:
#                 if fvalue in value:
#                     selstr = 'selected="selected"'
#             elif fvalue == value:
#                 selstr = 'selected="selected"'
#
#             inpu += '  <option value="%s" %s>%s</option>\n' % \
#                     (fvalue, selstr, flabel)
#
#         inpu += '\n</select>'
#
#         return self.__fieldfmt % {'label': label, 'inputs': inpu}
#
#     def render_DateField( self, field, value ):
#         return self.render_Field(field, value, 'text')
#
#     def render_FileUploadField( self, field, value ):
#         return self.render_Field(field, value, 'file')
#


# - Include this text in the simple rendering code (maybe in the fields
#   themselves):
#
#      Choices
#      -------
#
#      exactly 1 : radio buttons  OR  menu (without multiple option)
#          <input name='name' type='radio' value='1'/>
#          <input name='name' type='radio' value='2'/>
#          <input name='name' type='radio' value='3'/>
#
#          <select name='name'>
#          <option value='1' />
#          <option value='2' />
#          <option value='3' />
#          </select>
#
#
#      0 or many: checkboxes  OR  menu (with multiple option)
#          <input name='name' type='checkbox' value='1'/>
#          <input name='name' type='checkbox' value='2'/>
#          <input name='name' type='checkbox' value='3'/>
#
#          <select name='name' multiple='1' size='3'>
#              <!-- size has to be >1 if multiple is used -->
#          <option value='1' />
#          <option value='2' />
#          <option value='3' />
#          </select>

