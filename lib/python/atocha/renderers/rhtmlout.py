#!/usr/bin/env python
#
# $Id$
#

"""
Renderer for forms using htmlout.
"""

# stdlib imports.
from os.path import join

# atocha imports.
import atocha
from atocha.render import FormRenderer
from atocha.field import ORI_VERTICAL
from atocha.fields.uploads import FileUploadField
from atocha.messages import msg_type

# htmlout imports.
try:
    from htmlout import *
except ImportError:
    raise SystemExit(
        'Error: You need to install the htmlout library to use this module.')


__all__ = ['HoutFormRenderer', 'HoutDisplayRenderer']


#-------------------------------------------------------------------------------
#
class HoutRenderer(FormRenderer):
    """
    Base class for all renderers that will output to htmlout.
    """

    # Default encoding for output.
    default_encoding = None # Default: to unicode.

    # CSS classes.
    css_errors = u'atoerror'
    css_table = u'atotable'
    css_label = u'atolabel'

    def __init__( self, *args, **kwds ):
        """
        Grab the encoding parameter on top of the basic form renderer
        construction parameters.
        """

        try:
            self.label_semicolon = kwds['labelsemi']
            del kwds['labelsemi']
        except KeyError:
            self.label_semicolon = False
        """Whether we automatically add a semicolon to the labels or not."""

        FormRenderer.__init__(self, *args, **kwds)

    def do_table( self, pairs=(), extra=None ):
        table = TABLE(CLASS=self.css_table)
        for label, inputs in pairs:
            assert isinstance(label, (unicode, list))
            assert isinstance(inputs, (unicode, list))

            if self.label_semicolon:
                label.tail += ':'
            table.append(TR(
                TD(label, CLASS=self.css_label),
                TD(inputs, CLASS=self.css_input) ))
        if extra:
            assert isinstance(extra, list)
            table.append(extra)
        return table

    def _geterror( self, errmsg ):
        if errmsg:
            assert isinstance(errmsg, unicode)
            return [SPAN(errmsg, CLASS=self.css_errors), BR()]
        else:
            return []



#-------------------------------------------------------------------------------
#
class HoutFormRenderer(HoutRenderer):
    """
    Form renderer that outputs htmlout nodes.

    See FormRenderer class for full details.
    """

    # CSS classes.
    css_input = u'atoinput'
    css_required = u'atorequired'
    css_vertical = u'atominitable'
    
    scriptsdir = None

    def do_render( self, fields, action, submit ):
        # Create the form container.
        hform = self.do_render_container(action)

        # Create and append the table contained inside.
        hform.append( self.do_render_table(fields) )

        # Create and append the submit buttons.
        hform.append( self.render_submit(submit) )

        # Note: we don't do anything explicit about the scripts and notices.

        # Return the form container.
        return hform

    def do_render_container( self, action ):
        form = self._form

        if action is None:
            raise RuntimeError('Error: You must specify a non-null action '
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

        return FORM(dict(opts))

    def do_render_table( self, fields ):
        hidden, visible = [], []
        for field in fields:
            rendered = self._render_field(field)
            if field.ishidden():
                hidden.extend(rendered)
            else:
                label = self._get_label(field)
                if field.isrequired():
                    label = [label, SPAN('*', CLASS=self.css_required)]
                visible.append( (label, rendered) )

        return self.do_table(visible, hidden)

    def do_render_submit( self, submit, reset ):
        nodes = []
        if isinstance(submit, msg_type):
            nodes.append(INPUT(type='submit', value=_(submit)))
        else:
            assert isinstance(submit, (list, tuple))
            for value, name in submit:
                nodes.append(INPUT(type='submit', name=name, value=_(value)))
        if reset:
            nodes.append(INPUT(type='reset', value=_(reset)))
        return nodes

    def do_render_scripts( self, scripts ):
        nodes = []
        if not scripts:
            return nodes
        
        scriptsdir = self.scriptsdir or ''
        for fn, notice in scripts.iteritems():
            nodes.append( SCRIPT(notice,
                                 language="JavaScript",
                                 src=join(scriptsdir, fn),
                                 type="text/javascript"))
        return nodes

    #---------------------------------------------------------------------------

    def renderHidden( self, field, rvalue ):
        inputs = []
        # Use the first variable name.
        varname = field.varnames[0]

        if isinstance(rvalue, unicode):
            inputs.append(
                INPUT(name=varname, type="hidden", value=rvalue))
        elif isinstance(rvalue, list):
            for rval in rvalue:
                inputs.append(
                    INPUT(name=varname, type="hidden", value=rval))
        else:
            raise RuntimeError("Error: unexpected type '%s' for rendering." %
                               type(rvalue))

        return inputs


    def _input( self, htmltype, field, value, checked=False, label=None,
                varname=None ):
        """
        Render an html input.
        """
        if varname is None:
            varname = field.varnames[0]

        inpu = INPUT(name=varname, type=htmltype, CLASS=field.css_class)

        if value:
            inpu.attrib['value'] = value
        if label is not None:
            inpu.text = label
        if checked:
            inpu.attrib['checked'] = '1'            
        if hasattr(field, 'size') and field.maxlen is not None:
            inpu.attrib['size'] = str(field.size)
        if hasattr(field, 'maxlen') and field.maxlen is not None:
            inpu.attrib['maxlength'] = str(field.maxlen)

        return inpu

    def _single( self, htmltype, field, value, errmsg,
                 checked=False, label=None, varname=None ):
        """
        Render a single field.
        Returns a list.
        """
        return self._geterror(errmsg) + \
               [self._input(htmltype, field, value, checked, label, varname)]

    def _orient( self, field, inputs ):
        """
        Place the given list of inputs in a small vertical table if necessary.
        """
        if field.orient is ORI_VERTICAL:
            table = TABLE(CLASS=self.css_vertical)
            for i in inputs:
                table.append(TR(TD(i)))
            return [table]
        else:
            return inputs

    def renderStringField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

    def renderTextAreaField( self, field, rvalue, errmsg, required ):
        text = TEXTAREA(rvalue, name=field.varnames[0], CLASS=field.css_class)
        if field.rows:
            text.attrib['rows'] = str(field.rows)
        if field.cols:
            text.attrib['cols'] = str(field.cols)
        return [self._geterror(errmsg), text]

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

    renderAgreeField = renderBoolField

    def renderRadioField( self, field, rvalue, errmsg, required ):
        assert rvalue is not None
        inputs = []
        for vname, label in field.choices:
            checked = bool(vname == rvalue)
            inputs.append(
                self._input('radio', field, vname, checked, _(label)))
        output = self._orient(field, inputs)
        return [self._geterror(errmsg)] + output

    def _renderMenu( self, field, rvalue, errmsg, required,
                     multiple=None, size=None ):
        "Render a SELECT menu. 'rvalue' is expected to be a list of values."

        select = SELECT(name=field.varnames[0], CLASS=field.css_class)
        if size is not None and size > 1:
            select.attrib['size'] = str(field.size)
        if multiple:
            select.attrib['multiple'] = '1'

        for vname, label in field.choices:
            option = OPTION(_(label), value=vname)
            if vname in rvalue:
                option.attrib['selected'] = "selected"
            select.append(option)
        return [self._geterror(errmsg), select]

    def renderMenuField( self, field, rvalue, errmsg, required ):
        return self._renderMenu(field, [rvalue], errmsg, required)

    def renderCheckboxesField( self, field, rvalue, errmsg, required ):
        inputs = []
        for vname, label in field.choices:
            checked = vname in rvalue
            inputs.append(self._input('checkbox', field, vname, checked, _(label)))
        output = self._orient(field, inputs)
        return [self._geterror(errmsg)] + output

    def renderListboxField( self, field, rvalue, errmsg, required ):
        assert rvalue is not None
        if not isinstance(rvalue, list):
            rvalue = [rvalue] # May be a str if not multiple.
        return self._renderMenu(field, rvalue, errmsg, required,
                                field.multiple, field.size)

    def renderFileUploadField( self, field, rvalue, errmsg, required ):
        return self._single('file', field, rvalue, errmsg)

    def renderSetFileField( self, field, rvalue, errmsg, required ):
        filew = self._single('file', field, rvalue, errmsg)
        resetw = self._single('checkbox', field, u'1', errmsg, rvalue,
                              varname=field.varnames[1])
        return [filew, _(field.remlabel), resetw]

    def _script( self, field, errmsg, script, noscript=None ):
        "Render a script widget."
        varname = field.varnames[0]
        # Note: setting 'name' on a SCRIPT tag is not standard, but it allows us
        # to render the errors later on.
        lines = [ SCRIPT(script, name=varname, CLASS=field.css_class) ]
        if noscript:
            lines.append( NOSCRIPT(noscript, name=varname,
                                   CLASS=field.css_class) )
        return [self._geterror(errmsg)] + lines

    def renderJSDateField( self, field, rvalue, errmsg, required ):
        varname = field.varnames[0]
        fargs = (varname, rvalue and ", '%s'" % rvalue or '')
        script = (u"DateInput('%s', true, 'YYYYMMDD'%s);"
                  u"hideInputs(this);") % fargs

        # We must be able to accept both the string version and the datetime
        # version because of the different paths of argument parsing... it's
        # possible that we get asked to render something using values that have
        # not been parsed previously (for example, during the automated form
        # parsing errors).
        noscript = INPUT(name=varname, value=rvalue or '')

        return self._script(field, errmsg, script, noscript)



#-------------------------------------------------------------------------------
#
class HoutDisplayRenderer(HoutRenderer):
    """
    Display renderer in normal text. This renderer is meant to display parsed
    values as a read-only table, and not as an editable form.

    Note: we do not render the errors.
    """

    # CSS classes.
    css_input = u'atodisplay'

    def __init__( self, *args, **kwds ):
        try:
            self.show_hidden = kwds['show_hidden']
            del kwds['show_hidden']
        except KeyError:
            self.show_hidden = True # Default is to display.
        """Determines whether we render the fields that are hidden."""

        HoutRenderer.__init__(self, *args, **kwds)

    def do_render( self, fields, action, submit ):
        # We only need return the table.
        return self.do_render_table(fields)

    def do_render_container( self, action ):
        return None

    def do_render_table( self, fields ):
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

        return self.do_table(visible)

    def do_render_submit( self, submit, reset ):
        return None

    def do_render_scripts( self ):
        return None

    #---------------------------------------------------------------------------

    def renderHidden( self, field, rvalue ):
        return None

    def _simple( self, field, value, errmsg, required ):
        """
        Render a simple field with the given parameters.
        """
        return [value]

    renderStringField = _simple

    def renderTextAreaField( self, field, value, errmsg, required ):
        return [PRE(value)]

    renderPasswordField = _simple
    renderDateField = _simple

    def renderEmailField( self, field, value, errmsg, required ):
        if value:
            return [A(value, href='mailto:%s' % value)]
        return []

    def renderURLField( self, field, value, errmsg, required ):
        if value:
            return [A(value, href='%s' % value)]
        return []
        
    renderIntField = _simple
    renderFloatField = _simple
    renderBoolField = _simple
    renderAgreeField = renderBoolField
    renderRadioField = _simple
    renderMenuField = _simple
    renderCheckboxesField = _simple
    renderListboxField = _simple

    def renderFileUploadField( self, field, value, errmsg, required ):
        # Never display a file upload. Don't even try.
        return []

    renderSetFileField = renderFileUploadField

    renderJSDateField = _simple

