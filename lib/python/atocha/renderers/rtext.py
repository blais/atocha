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
Simple text-based form renderers.
"""

# stdlib imports.
import StringIO, codecs
from os.path import join

# atocha imports.
from atocha import AtochaError, AtochaInternalError
import atocha.render
from atocha.field import Field, ORI_VERTICAL
from atocha.fields import *
from atocha.messages import msg_type


__all__ = ['TextFormRenderer', 'TextDisplayRenderer']


#-------------------------------------------------------------------------------
#
class TextRenderer(atocha.render.FormRenderer):
    """
    Base class for all renderers that will output to text.
    """

    # Default encoding for output.
    default_encoding = None # Default: to unicode.

    # CSS classes.
    css_errors = u'atoerr'
    css_table = u'atotbl'
    css_label = u'atolbl'

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

        atocha.render.FormRenderer.__init__(self, *args, **kwds)


    def _create_buffer( self ):
        """
        Create the default file for output.
        """
        sio = StringIO.StringIO()
        if self.outenc is not None:
            Writer = codecs.getwriter(self.outenc)
            sio = Writer(sio)
        return sio

    def do_table( self, pairs=(), extra=None, css_class=None ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()

        css = [self.css_table]
        if css_class:
            css.append(css_class)
        f.write(u'<table class=%s>' % ' '.join(css))
        for label, inputs in pairs:
            assert isinstance(label, unicode)
            assert isinstance(inputs, unicode)

            if self.label_semicolon:
                label += ':'
            f.write((u'<tr><td class="%s">%s</td>\n'
                     u'    <td class="%s">%s</td></tr>\n') %
                    (self.css_label, label, self.css_input, inputs or u''))
        if extra:
            assert isinstance(extra, unicode)
            f.write(extra)
            f.write(u'\n')
        f.write(u'</table>\n')

        if self.ofile is None: return f.getvalue()




#-------------------------------------------------------------------------------
#
class TextFormRenderer(TextRenderer):
    """
    Form renderer that outputs HTML text directly.

    See FormRenderer class for full details.
    """

    # Registry for renderer.
    renderers_registry = {}

    # CSS classes.
    css_input = u'atoinp'
    css_submit = u'atosub'
    css_required = u'atoreq'
    css_vertical = u'atomini'

    scriptsdir = None

    def _geterror( self, renctx ):
        if renctx.errmsg:
            assert isinstance(renctx.errmsg, unicode)
            return (u'<span class="%s">%s</span><br/>' %
                    (self.css_errors, renctx.errmsg))
        else:
            return u''

    def do_render( self, fields, action, submit ):
        try:
            # File object that gets set as a side-effect.
            self.ofile = f = self._create_buffer()

            # (Side-effect will add to the file.)
            self.do_render_container(action)

            # (Side-effect will add to the file.)
            self.do_render_table(fields)

            # Render submit buttons.
            self.render_submit(submit)

            # Close the form (the container rendering only outputs the header.
            f.write(self.close_container())

        finally:
            self.ofile = None

        # Note: we don't do anything explicit about the scripts and notices.

        # Return the string for the entire form.
        return f.getvalue()


    def do_render_container( self, action ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()
        form = self._form

        if action is None:
            raise AtochaError('Error: You must specify a non-null action '
                               'for rendering this form.')

        # Other options.
        opts = [('id', form.name),
                ('name', form.name),
                ('action', action),
                ('method', form.method),]
        if form.accept_charset is not None:
            opts.append(('accept-charset', form.accept_charset))
        if form.enctype is not None:
            opts.append(('enctype', form.enctype))

        f.write(u'<form %s>\n' %
                ' '.join(['%s="%s"' % x for x in opts]).decode('ascii'))

        if self.ofile is None: return f.getvalue()

    def close_container( self ):
        return u'</form>'

    def do_render_table( self, fields, css_class=None ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()

        hidden, visible = [], []
        for field in fields:
            rendered = self._render_field(field, field.state)
            if field.ishidden():
                hidden.append(rendered)
            else:
                label = self._get_label(field)
                if field.isrequired():
                    label += u'<span class="%s">*</span>' % self.css_required
                visible.append( (label, rendered) )

        self.do_table(visible, u'\n'.join(hidden), css_class=css_class)

        if self.ofile is None: return f.getvalue()

    def do_render_submit( self, submit, reset ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()
        f.write(u'<div class="%s">\n' % self.css_submit)

        if isinstance(submit, msg_type):
            f.write(u'<input type="submit" value="%s" />\n' % (_(submit)))
        else:
            assert isinstance(submit, (list, tuple))
            for subvalue, label in submit:
                assert isinstance(label, msg_type)
                f.write((u'<input type="submit" name="%s" value="%s" />\n') %
                        (subvalue, _(label)))

        if reset:
            f.write(u'<input type="reset" value="%s" />\n' % _(reset))

        f.write(u'</div>\n')
        if self.ofile is None: return f.getvalue()

    def do_render_scripts( self, scripts ):
        if not scripts:
            return u''

        f = self._create_buffer()
        scriptsdir = self.scriptsdir or ''
        for fn, notice in scripts.iteritems():
            f.write(u'<script language="JavaScript" '
                    u'src="%s" ' % join(scriptsdir, fn) +
                    u'type="text/javascript">\n')
            if notice:
                f.write(notice)
                f.write(u'\n')
            f.write(u'</script>\n')
        return f.getvalue()

    #---------------------------------------------------------------------------

    def _input( self, htmltype, field, state, value,
                checked=False, label=None, varname=None ):
        """
        Render an html input.
        """
        if varname is None:
            varname = field.varnames[0]

        opts = [('name', varname),
                ('type', htmltype),
                ('class', field.css_class),]
        if checked:
            opts.append( ('checked', '1') )
        if getattr(field, 'size', None):
            opts.append( ('size', field.size) )
        if getattr(field, 'maxlen', None):
            opts.append( ('maxlength', field.maxlen) )

        if state is Field.DISABLED:
            opts.append( ('disabled', '1') )
        elif state is Field.READONLY:
            opts.append( ('readonly', '1') )
        else:
            assert state is Field.NORMAL

        if getattr(field, 'onchange', None):
            # Note: we transparently translate to a more portable onclick callback.
            opts.append( ('onclick', field.onchange) )

        o = u'<input ' + ' '.join(['%s="%s"' % x for x in opts]).decode('ascii')
        if value:
            o += u' value="%s"' % value
        if label is not None:
            o += u'>%s</input>' % label
        else:
            o += u'/>'
        return o

    def _single( self, htmltype, field, renctx,
                 checked=False, label=None, varname=None ):
        """
        Render a single field.
        """
        return self._geterror(renctx) + \
               self._input(htmltype, field,
                           renctx.state, renctx.rvalue,
                           checked, label, varname)

    def _orient( self, field, inputs ):
        """
        Place the given list of inputs in a small vertical table if necessary.
        """
        if field.orient is ORI_VERTICAL:
            s = StringIO.StringIO()
            s.write(u'<table class="%s">\n' % self.css_vertical)
            for i in inputs:
                s.write(u'<tr><td>%s</td></tr>\n' % i)
            s.write(u'</table>\n')
            return s.getvalue()
        else:
            return u'\n'.join(inputs)

    def _renderMenu( self, field, renctx, multiple=None, size=None ):
        "Render a SELECT menu. 'rvalue' is expected to be a list of values."

        selopts = []
        if size is not None and size > 1:
            selopts.append('size="%d"' % field.size)
        if multiple:
            selopts.append('multiple="1"')

        if renctx.state is Field.DISABLED:
            selopts.append( ('disabled="1"') )
        elif renctx.state is Field.READONLY:
            selopts.append( ('readonly="1"') )
        else:
            assert renctx.state is Field.NORMAL

        if getattr(field, 'onchange', None):
            selopts.append( ('onchange', field.onchange) )

        lines = []
        lines.append(
            u'<select name="%s" %s class="%s">' %
            (field.varnames[0], ' '.join(selopts), field.css_class))
        for vname, label in field.choices:
            selstr = u''
            if vname in renctx.rvalue:
                selstr = u'selected="selected"'
            lines.append(u'<option value="%s" %s>%s</option>' %
                         (vname, selstr, _(label)))
        lines.append(u'</select>')
        return self._geterror(renctx) + u'\n'.join(lines)

    def _script( self, field, renctx, script, noscript=None ):
        """
        Render a script widget.
        """
        varname = field.varnames[0]
        # Note: setting 'name' on a SCRIPT tag is not standard, but it allows us
        # to render the errors later on.
        lines = [
            u'<script name="%s" class="%s">' % (varname, field.css_class),
            script,
            u'</script>']
        if noscript:
            lines.extend([
                u'<noscript name="%s" class="%s">' % (varname, field.css_class),
                noscript,
                u'</noscript>'])
        return self._geterror(renctx) + u'\n'.join(lines)


    #---------------------------------------------------------------------------

    def renderHidden( rdr, field, rvalue ):
        inputs = []
        # Use the first variable name.
        varname = field.varnames[0]

        if isinstance(rvalue, unicode):
            inputs.append(u'<input name="%s" type="hidden" value="%s" />' %
                          (varname.decode('ascii'), rvalue))
        elif isinstance(rvalue, list):
            for rval in rvalue:
                inputs.append(u'<input name="%s" type="hidden" value="%s" />' %
                              (varname.decode('ascii'), rval))
        else:
            raise AtochaInternalError(
                "Error: unexpected type '%s' for rendering." % type(rvalue))

        return u'\n'.join(inputs)

#-------------------------------------------------------------------------------
#
def renderStringField( rdr, field, renctx ):
    return rdr._single('text', field, renctx)

def renderTextAreaField( rdr, field, renctx ):
    opts = []
    if field.rows:
        opts.append( ('rows', field.rows) )
    if field.cols:
        opts.append( ('cols', field.cols) )

    if renctx.state is Field.DISABLED:
        opts.append( ('disabled', 1) )
    elif renctx.state is Field.READONLY:
        opts.append( ('readonly', 1) )
    else:
        assert renctx.state is Field.NORMAL

    return (rdr._geterror(renctx) +
            u'<textarea name="%s" %s class="%s">%s</textarea>' %
            (field.varnames[0].decode('ascii'),
             ' '.join(['%s="%d"' % x for x in opts]).decode('ascii'),
             field.css_class.decode('ascii'), renctx.rvalue or u''))

def renderPasswordField( rdr, field, renctx ):
    return rdr._single('password', field, renctx)

def renderBoolField( rdr, field, renctx ):
    # The render type calls for any value and for the rvalue to determine
    # whether this will get checked or not.
    checked, renctx.rvalue = renctx.rvalue, u'1'
    return rdr._single('checkbox', field, renctx, checked)

def renderRadioField( rdr, field, renctx ):
    assert renctx.rvalue is not None
    inputs = []
    for vname, label in field.choices:
        checked = bool(vname == renctx.rvalue)
        inputs.append(
            rdr._input('radio', field, renctx.state,
                        vname, checked, _(label)))
    output = rdr._orient(field, inputs)
    return rdr._geterror(renctx) + output

def renderMenuField( rdr, field, renctx ):
    renctx.rvalue = [renctx.rvalue]
    return rdr._renderMenu(field, renctx)

def renderCheckboxesField( rdr, field, renctx ):
    inputs = []
    for vname, label in field.choices:
        checked = vname in renctx.rvalue
        inputs.append(
            rdr._input('checkbox', field, renctx.state,
                        vname, checked, _(label)))
    output = rdr._orient(field, inputs)
    return rdr._geterror(renctx) + output

def renderListboxField( rdr, field, renctx ):
    assert renctx.rvalue is not None
    if not isinstance(renctx.rvalue, list):
        renctx.rvalue = [renctx.rvalue] # May be a str if not multiple.
    return rdr._renderMenu(field, renctx, field.multiple, field.size)

def renderFileUploadField( rdr, field, renctx ):
    return rdr._single('file', field, renctx)

def renderSetFileField( rdr, field, renctx ):
    filew = rdr._single('file', field, renctx)
    checked, renctx.rvalue = renctx.rvalue, u'1'
    resetw = rdr._single('checkbox', field, renctx,
                          checked, varname=field.varnames[1])
    return u'\n'.join([filew, '&nbsp;' + _(field.remlabel) + resetw])

def renderJSDateField( rdr, field, renctx ):
    varname = field.varnames[0]
    fargs = (varname, renctx.rvalue and ", '%s'" % renctx.rvalue or '')
    script = (u"DateInput('%s', true, 'YYYYMMDD' %s);"
              u"hideInputs(this);") % fargs

    # We must be able to accept both the string version and the datetime
    # version because of the different paths of argument parsing... it's
    # possible that we get asked to render something using values that have
    # not been parsed previously (for example, during the automated form
    # parsing errors).
    noscript = (u'<input name="%s" value="%s"/>' %
                (varname, renctx.rvalue or ''))

    return rdr._script(field, renctx, script, noscript)


#-------------------------------------------------------------------------------
# Register rendering routines.
TextFormRenderer_routines = ((StringField, renderStringField),
                             (TextAreaField, renderTextAreaField),
                             (PasswordField, renderPasswordField),
                             (DateField, renderStringField),
                             (EmailField, renderStringField),
                             (URLField, renderStringField),
                             (IntField, renderStringField),
                             (FloatField, renderStringField),
                             (BoolField, renderBoolField),
                             (AgreeField, renderBoolField),
                             (RadioField, renderRadioField),
                             (MenuField, renderMenuField),
                             (CheckboxesField, renderCheckboxesField),
                             (ListboxField, renderListboxField),
                             (FileUploadField, renderFileUploadField),
                             (SetFileField, renderSetFileField),
                             (JSDateField, renderJSDateField),)

for fcls, fun in TextFormRenderer_routines:
    atocha.render.register_render_routine(TextFormRenderer, fcls, fun)



#-------------------------------------------------------------------------------
#
class TextDisplayRenderer(TextRenderer, atocha.render.DisplayRendererBase):
    """
    Display renderer in normal text. This renderer is meant to display parsed
    values as a read-only table, and not as an editable form.

    Note: we do not render the errors.
    """

    # Registry for renderer.
    renderers_registry = {}

    # CSS classes.
    css_label = u'atodlbl'
    css_input = u'atodval'

    def __init__( self, *args, **kwds ):
        atocha.render.DisplayRendererBase.__init__(self, kwds)
        TextRenderer.__init__(self, *args, **kwds)

    def do_render( self, fields, action, submit ):
        form = self._form
        try:
            # File object that gets set as a side-effect.
            self.ofile = f = self._create_buffer()

            # (Side-effect will add to the file.)
            self.do_render_table(fields)

            # Close the form (the container rendering only outputs the header.
            f.write('</form>\n')
        finally:
            self.ofile = None

        return f.getvalue()

    def do_render_container( self, action ):
        return ''

    def do_render_table( self, fields, css_class=None ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()

        self.do_render_display_table(fields, css_class=css_class)

        if self.ofile is None: return f.getvalue()

    def do_render_submit( self, submit, reset ):
        return ''

    def do_render_scripts( self ):
        return ''

    def renderHidden( rdr, field, rvalue ):
        return ''


#-------------------------------------------------------------------------------
#
def displayValue( rdr, field, renctx ):
    return renctx.rvalue

def displayTextAreaField( rdr, field, renctx ):
    return u'<pre>%s</pre>' % renctx.rvalue

def displayEmailField( rdr, field, renctx ):
    if renctx.rvalue:
        return u'<a href="mailto:%s">%s</a>' % (renctx.rvalue,
                                                renctx.rvalue)
    return u''

def displayURLField( rdr, field, renctx ):
    if renctx.rvalue:
        return u'<a href="%s">%s</a>' % (renctx.rvalue,
                                         renctx.rvalue)
    return u''

def displayFileUploadField( rdr, field, renctx ):
    # Never display a file upload. Don't even try.
    return u''

#-------------------------------------------------------------------------------
# Register rendering routines.
TextDisplayRenderer_routines = ((StringField, displayValue),
                                (TextAreaField, displayTextAreaField),
                                (PasswordField, displayValue),
                                (DateField, displayValue),
                                (EmailField, displayEmailField),
                                (URLField, displayURLField),
                                (IntField, displayValue),
                                (FloatField, displayValue),
                                (BoolField, displayValue),
                                (AgreeField, displayValue),
                                (RadioField, displayValue),
                                (MenuField, displayValue),
                                (CheckboxesField, displayValue),
                                (ListboxField, displayValue),
                                (FileUploadField, displayFileUploadField),
                                (SetFileField, displayFileUploadField),
                                (JSDateField, displayValue),)

for fcls, fun in TextDisplayRenderer_routines:
    atocha.render.register_render_routine(TextDisplayRenderer, fcls, fun)

