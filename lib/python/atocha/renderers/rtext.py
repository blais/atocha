#!/usr/bin/env python
#
# $Id$
#

"""
Simple text-based form renderers.
"""

# stdlib imports.
import StringIO, codecs
from os.path import join

# atocha imports.
from atocha.render import FormRenderer
from atocha.fields import ORI_VERTICAL, FileUploadField
from atocha.messages import msg_type


__all__ = ['TextFormRenderer', 'TextDisplayRenderer']


#-------------------------------------------------------------------------------
#
class TextRenderer(FormRenderer):
    """
    Base class for all renderers that will output to text.
    """

    # Default encoding for output.
    default_encoding = None # Default: to unicode.

    # CSS classes.
    css_errors = u'formerror'
    css_table = u'formtable'
    css_label = u'formlabel'

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


    def _create_buffer( self ):
        """
        Create the default file for output.
        """
        sio = StringIO.StringIO()
        if self.outenc is not None:
            Writer = codecs.getwriter(self.outenc)
            sio = Writer(sio)
        return sio

    def do_table( self, pairs=(), extra=None ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()

        f.write(u'<table class=%s>' % self.css_table)
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

    def _geterror( self, errmsg ):
        if errmsg:
            assert isinstance(errmsg, unicode)
            return (u'<span class="%s">%s</span><br/>' %
                    (self.css_errors, errmsg))
        else:
            return u''



#-------------------------------------------------------------------------------
#
class TextFormRenderer(TextRenderer):
    """
    Form renderer that outputs HTML text directly.

    See FormRenderer class for full details.
    """

    # CSS classes.
    css_input = u'forminput'
    css_required = u'formreq'
    css_vertical = u'formminitable'

    scriptsdir = None

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
            raise RuntimeError('Error: You must specify a non-null action '
                               'for rendering this form.')

        # Other options.
        opts = [('id', form.name),
                ('name', form.name),
                ('action', form.action),
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

    def do_render_table( self, fields ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()

        hidden, visible = [], []
        for field in fields:
            rendered = self._render_field(field)
            if field.ishidden():
                hidden.append(rendered)
            else:
                label = self._get_label(field)
                if field.isrequired():
                    label += u'<span class="%s">*</span>' % self.css_required
                visible.append( (label, rendered) )

        self.do_table(visible, u'\n'.join(hidden))

        if self.ofile is None: return f.getvalue()

    def do_render_submit( self, submit, reset ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()

        if isinstance(submit, msg_type):
            f.write(u'<input type="submit" value="%s" />\n' % _(submit))
        else:
            assert isinstance(submit, (list, tuple))
            for value, name in submit:
                f.write(u'<input type="submit" name="%s" value="%s" />\n' %
                        (name, _(value)))

        if reset:
            f.write(u'<input type="reset" value="%s" />\n' % _(reset))

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

    def renderHidden( self, field, rvalue ):
        inputs = []

        if isinstance(rvalue, unicode):
            inputs.append(u'<input name="%s" type="hidden" value="%s" />' %
                          (field.name.decode('ascii'), rvalue))
        elif isinstance(rvalue, list):
            for rval in rvalue:
                inputs.append(u'<input name="%s" type="hidden" value="%s" />' %
                              (field.name.decode('ascii'), rval))
        else:
            raise RuntimeError("Error: unexpected type '%s' for rendering." %
                               type(rvalue))

        return u'\n'.join(inputs)


    def _input( self, htmltype, field, value, checked=False, label=None ):
        """
        Render an html input.
        """
        if checked:
            checkstr = u'checked="1"'
        else:
            checkstr = u''

        fargs = (field.name.decode('ascii'),
                 htmltype.decode('ascii'),
                 value or u'',
                 field.css_class.decode('ascii'),
                 checkstr)

        if label is not None:
            o = (u'<input name="%s" type="%s" value="%s" class="%s" %s>'
                 u'%s</input>') % (fargs + (label,))
        else:
            o = (u'<input name="%s" type="%s" value="%s" class="%s" %s/>' %
                 fargs)
        return o

    def _single( self, htmltype, field, value, errmsg,
                 checked=False, label=None ):
        """
        Render a single field.
        """
        return self._geterror(errmsg) + \
               self._input(htmltype, field, value, checked, label)

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

    def renderStringField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

    def renderTextAreaField( self, field, rvalue, errmsg, required ):
        rowstr = field.rows and u' rows="%d"' % field.rows or u''
        colstr = field.cols and u' cols="%d"' % field.cols or u''
        return (self._geterror(errmsg) +
                u'<textarea name="%s" %s %s class="%s">%s</textarea>' %
                (field.name.decode('ascii'), rowstr, colstr,
                 field.css_class.decode('ascii'), rvalue or u''))

    def renderPasswordField( self, field, rvalue, errmsg, required ):
        return self._single('password', field, rvalue, errmsg)

    def renderDateField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

    def renderEmailField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

    def renderURLField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

    def renderIntField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

    def renderFloatField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

    def renderBoolField( self, field, rvalue, errmsg, required ):
        # The render type calls for any value and for the rvalue to determine
        # whether this will get checked or not.
        return self._single('checkbox', field, u'1', errmsg, rvalue)

    def renderRadioField( self, field, rvalue, errmsg, required ):
        assert rvalue is not None
        inputs = []
        for vname, label in field.values:
            checked = bool(vname == rvalue)
            inputs.append(
                self._input('radio', field, vname, checked, _(label)))
        output = self._orient(field, inputs)
        return self._geterror(errmsg) + output

    def _renderMenu( self, field, rvalue, errmsg, required,
                     multiple=None, size=None ):
        "Render a SELECT menu. 'rvalue' is expected to be a list of values."

        selopts = []
        if size is not None and size > 1:
            selopts.append('size="%d"' % field.size)
        if multiple:
            selopts.append('multiple="1"')

        lines = []
        lines.append(
            u'<select name="%s" %s class="%s">' %
            (field.name, ' '.join(selopts), field.css_class))
        for vname, label in field.values:
            selstr = u''
            if vname in rvalue:
                selstr = u'selected="selected"'
            lines.append(u'<option value="%s" %s>%s</option>' %
                         (vname, selstr, _(label)))
        lines.append(u'</select>')
        return self._geterror(errmsg) + u'\n'.join(lines)

    def renderMenuField( self, field, rvalue, errmsg, required ):
        return self._renderMenu(field, [rvalue], errmsg, required)

    def renderCheckboxesField( self, field, rvalue, errmsg, required ):
        inputs = []
        for vname, label in field.values:
            checked = vname in rvalue
            inputs.append(self._input('checkbox', field, vname, checked, _(label)))
        output = self._orient(field, inputs)
        return self._geterror(errmsg) + output

    def renderListboxField( self, field, rvalue, errmsg, required ):
        assert rvalue is not None
        if not isinstance(rvalue, list):
            rvalue = [rvalue] # May be a str if not multiple.
        return self._renderMenu(field, rvalue, errmsg, required,
                                field.multiple, field.size)

    def renderFileUploadField( self, field, rvalue, errmsg, required ):
        return self._single('file', field, rvalue, errmsg)

    def _script( self, field, errmsg, script, noscript=None ):
        "Render a script widget."
        # Note: setting 'name' on a SCRIPT tag is not standard, but it allows us
        # to render the errors later on.
        lines = [
            u'<script name="%s" class="%s">' % (field.name, field.css_class),
            script,
            u'</script>']
        if noscript:
            lines.extend([
                u'<noscript class="%s">' % field.css_class,
                noscript,
                u'</noscript>'])
        return self._geterror(errmsg) + u'\n'.join(lines)

    def renderJSDateField( self, field, rvalue, errmsg, required ):
        fargs = (field.name, rvalue and ", '%s'" % rvalue or '')
        script = (u"DateInput('%s', true, 'YYYYMMDD' %s);"
                  u"hideInputs(this);") % fargs

        # We must be able to accept both the string version and the datetime
        # version because of the different paths of argument parsing... it's
        # possible that we get asked to render something using values that have
        # not been parsed previously (for example, during the automated form
        # parsing errors).
        noscript = (u'<input name="%s" value="%s"/>' %
                    (field.name, rvalue or ''))

        return self._script(field, errmsg, script, noscript)





#-------------------------------------------------------------------------------
#
class TextDisplayRenderer(TextRenderer):
    """
    Display renderer in normal text. This renderer is meant to display parsed
    values as a read-only table, and not as an editable form.

    Note: we do not render the errors.
    """

    # CSS classes.
    css_input = u'formdisplay'

    def __init__( self, *args, **kwds ):
        try:
            self.show_hidden = kwds['show_hidden']
            del kwds['show_hidden']
        except KeyError:
            self.show_hidden = True # Default is to display.
        """Determines whether we render the fields that are hidden."""

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

    def do_render_table( self, fields ):
        # Use side-effect for efficiency if requested.
        f = self.ofile or self._create_buffer()

        visible = []
        for field in fields:
            # Don't display hidden fields.
            if not self.show_hidden and field.ishidden():
                continue

            # Never display a file upload. Don't even try.
            if isinstance(field, FileUploadField):
                continue

            rendered = self._display_field(field)
            visible.append( (self._get_label(field), rendered) )

        self.do_table(visible)

        if self.ofile is None: return f.getvalue()

    def do_render_submit( self, submit, reset ):
        return ''

    def do_render_scripts( self ):
        return ''

    #---------------------------------------------------------------------------

    def renderHidden( self, field, rvalue ):
        return ''

    def _simple( self, field, value, errmsg, required ):
        """
        Render a simple field with the given parameters.
        """
        return value

    renderStringField = _simple

    def renderTextAreaField( self, field, value, errmsg, required ):
        return u'<pre>%s</pre>' % value

    renderPasswordField = _simple
    renderDateField = _simple

    def renderEmailField( self, field, value, errmsg, required ):
        if value:
            return u'<a href="mailto:%s">%s</a>' % (value, value)
        return u''

    def renderURLField( self, field, value, errmsg, required ):
        if value:
            return u'<a href="%s">%s</a>' % (value, value)
        return u''
        
    renderIntField = _simple
    renderFloatField = _simple
    renderBoolField = _simple
    renderRadioField = _simple
    renderMenuField = _simple
    renderCheckboxesField = _simple
    renderListboxField = _simple

    def renderFileUploadField( self, field, value, errmsg, required ):
        # Never display a file upload. Don't even try.
        return u''

    renderJSDateField = _simple
