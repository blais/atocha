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
Renderer for forms using htmlout.
"""

# stdlib imports
from os.path import join

# atocha imports
from atocha import AtochaError, AtochaInternalError
import atocha.render
from atocha.field import *
from atocha.fields import *
from atocha.messages import msg_type

# htmlout imports
try:
    from htmlout import *
except ImportError:
    raise ImportError(
        'Error: You need to install the htmlout library to use this module.')


__all__ = ['HoutFormRenderer', 'HoutDisplayRenderer']


#-------------------------------------------------------------------------------
#
class HoutRenderer(atocha.render.FormRenderer):
    """
    Base class for all renderers that will output to htmlout.
    """

    # Default encoding for output.
    default_encoding = None # Default: to unicode.

    # CSS classes.
    css_errors = u'atoerr'
    css_table = u'atotbl'
    css_label = u'atolbl'

    # Default value.
    label_semicolon = False

    def __init__( self, *args, **kwds ):
        """
        Grab the encoding parameter on top of the basic form renderer
        construction parameters.
        """

        self.label_semicolon = kwds.pop('labelsemi',
                                        HoutRenderer.label_semicolon)
        """Whether we automatically add a semicolon to the labels or not."""

        atocha.render.FormRenderer.__init__(self, *args, **kwds)


    def do_table( self, pairs=(), extra=None, css_class=None ):
        """
        Implementation of instance method version of table().
        """
        return self.do_table_imp(self, pairs, extra, css_class)

    def do_ctable( cls, pairs=(), extra=None, css_class=None ):
        """
        Class method version of table().
        """
        return cls.do_table_imp(cls, pairs, extra, css_class)

    do_ctable = classmethod(do_ctable)

    def do_table_imp( rdr, pairs=(), extra=None, css_class=None ):
        """
        Static method version of table().
        """
        css = [rdr.css_table]
        if css_class:
            css.append(css_class)
        table = TABLE(CLASS=' '.join(css))

        for label, inputs in pairs:
            assert isinstance(label, (unicode, list))
            assert isinstance(inputs, (unicode, list))

            tdlabel = TD(label, CLASS=rdr.css_label)
            if rdr.label_semicolon:
                tdlabel.append(':')
            table.append(TR(
                tdlabel,
                TD(inputs, CLASS=rdr.css_input) ))
        if extra:
            assert isinstance(extra, list)
            table.append(extra)
        return table

    do_table_imp = staticmethod(do_table_imp)


#-------------------------------------------------------------------------------
#
class HoutFormRenderer(HoutRenderer):
    """
    Form renderer that outputs htmlout nodes.

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
            return [SPAN(renctx.errmsg, CLASS=self.css_errors), BR()]
        else:
            return []

    def do_render( self, fields, action, submit ):
        # Create the form container.
        hform = self.render_container(action)

        # Create and append the table contained inside.
        hform.append( self.do_render_table(fields) )

        # Create and append the submit buttons.
        hform.append( self.render_submit(submit) )

        # Note: we don't do anything explicit about the scripts and notices.

        # Return the form container.
        return hform

    def do_render_container( self, action_url ):
        form = self._form

        if action_url is None:
            raise AtochaError('Error: You must specify a non-null action '
                               'for rendering this form.')

        # Other options.
        opts = [('id', form.name),
                ('name', form.name),
                ('action', action_url),
                ('method', form.method),]
        if form.accept_charset is not None:
            opts.append(('accept-charset', form.accept_charset))
        if form.enctype is not None:
            opts.append(('enctype', form.enctype))

        return FORM(dict(opts))

    def do_render_table( self, fields, css_class=None ):
        hidden, visible = [], []
        for field in fields:
            rendered = self._render_field(field, field.state)
            if field.ishidden():
                hidden.extend(rendered)
            else:
                label = self._get_label(field)
                if field.isrequired():
                    label = [label, SPAN('*', CLASS=self.css_required)]
                visible.append( (label, rendered) )

        # Don't render a table if there are no visible widgets.
        if visible:
            return self.do_table(visible, hidden, css_class=css_class)
        else:
            return hidden

    def do_render_submit( self, submit, reset ):
        nodes = []
        if isinstance(submit, msg_type):
            nodes.append(INPUT(type='submit', value=_(submit)))
        else:
            assert isinstance(submit, (list, tuple))
            for subvalue, label in submit:
                assert isinstance(label, msg_type)
                nodes.append(INPUT(type='submit',
                                   name=subvalue, value=_(label)))
        if reset:
            nodes.append(INPUT(type='reset', value=_(reset)))
        return DIV(nodes, CLASS=self.css_submit)

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

    def _input( self, htmltype, field, state, value,
                checked=False, label=None, varname=None ):
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

        assert isinstance(checked, bool)
        if checked:
            inpu.attrib['checked'] = '1'
        if getattr(field, 'size', None):
            inpu.attrib['size'] = str(field.size)
        if getattr(field, 'maxlen', None):
            inpu.attrib['maxlength'] = str(field.maxlen)

        if state is Field.DISABLED:
            inpu.attrib['disabled'] = '1'
        elif state is Field.READONLY:
            inpu.attrib['readonly'] = '1'
        else:
            assert state is Field.NORMAL

        if getattr(field, 'onchange', None):
            # Note: we transparently translate to a more portable onclick
            # callback.
            inpu.attrib['onclick'] = field.onchange

        return inpu

    def _single( self, htmltype, field, renctx,
                 checked=False, label=None, varname=None ):
        """
        Render a single field.
        Returns a list.
        """
        return self._geterror(renctx) + \
               [self._input(htmltype, field,
                            renctx.state, renctx.rvalue,
                            checked, label, varname)]

    def _orient( self, field, inputs ):
        """
        Place the given list of inputs in a small vertical table if necessary.
        """
        if field.orient == ORI_VERTICAL:
            table = TABLE(CLASS=self.css_vertical)
            for i in inputs:
                table.append(TR(TD(i)))
            return [table]
        elif field.orient in (ORI_HORIZONTAL, ORI_RAW):
            return inputs
        else:
            assert False

    def _renderMenu( self, field, renctx, multiple=None, size=None ):
        "Render a SELECT menu. 'rvalue' is expected to be a list of values."

        select = SELECT(name=field.varnames[0], CLASS=field.css_class)
        if size is not None and size > 1:
            select.attrib['size'] = str(field.size)
        if multiple:
            select.attrib['multiple'] = '1'

        if renctx.state is Field.DISABLED:
            select.attrib['disabled'] = '1'
        elif renctx.state is Field.READONLY:
            select.attrib['readonly'] = '1'
        else:
            assert renctx.state is Field.NORMAL

        if getattr(field, 'onchange', None):
            select.attrib['onchange'] = field.onchange

        for vname, label in field.choices:
            option = OPTION(_(label), value=vname)
            if vname in renctx.rvalue:
                option.attrib['selected'] = "selected"
            select.append(option)
        return [self._geterror(renctx), select]

    def _script( self, field, renctx, script, noscript=None ):
        "Render a script widget."
        varname = field.varnames[0]
        # Note: setting 'name' on a SCRIPT tag is not standard, but it allows us
        # to render the errors later on.
        lines = [ SCRIPT(script, name=varname, CLASS=field.css_class) ]
        if noscript:
            lines.append( NOSCRIPT(noscript, name=varname,
                                   CLASS=field.css_class) )
        return [self._geterror(renctx)] + lines

    #---------------------------------------------------------------------------

    def renderHidden( rdr, field, rvalue ):
        inputs = []
        # Use the first variable name.
        varname = field.varnames[0]

        if isinstance(rvalue, unicode):
            inputs.append(
                INPUT(name=varname, type="hidden", value=rvalue))

        elif isinstance(rvalue, bool):
            inputs.append(
                INPUT(name=varname, type="hidden", value=rvalue and '1' or '0'))

        elif isinstance(rvalue, list):
            for rval in rvalue:
                inputs.append(
                    INPUT(name=varname, type="hidden", value=rval))
        else:
            raise AtochaInternalError(
                "Error: unexpected type '%s' for rendering field '%s'." %
                (type(rvalue), field.name))

        return inputs


#-------------------------------------------------------------------------------
#
def renderStringField( rdr, field, renctx ):
    return rdr._single('text', field, renctx)

def renderTextAreaField( rdr, field, renctx ):
    text = TEXTAREA(renctx.rvalue,
                    name=field.varnames[0],
                    CLASS=field.css_class)
    if field.rows:
        text.attrib['rows'] = str(field.rows)
    if field.cols:
        text.attrib['cols'] = str(field.cols)

    if renctx.state is Field.DISABLED:
        text.attrib['disabled'] = '1'
    elif renctx.state is Field.READONLY:
        text.attrib['readonly'] = '1'
    else:
        assert renctx.state is Field.NORMAL

    return [rdr._geterror(renctx), text]

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
    return [rdr._geterror(renctx)] + output

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
    return [rdr._geterror(renctx)] + output

def renderListboxField( rdr, field, renctx ):
    assert renctx.rvalue is not None
    if not isinstance(renctx.rvalue, list):
        renctx.rvalue = [renctx.rvalue] # May be a str if not multiple.
    return rdr._renderMenu(field, renctx, field.multiple, field.size)

def renderFileUploadField( rdr, field, renctx ):
    return rdr._single('file', field, renctx)

def renderSetFileField( rdr, field, renctx ):
    filew = rdr._single('file', field, renctx)
    checked, renctx.rvalue = False, u'1'
    resetw = rdr._single('checkbox', field, renctx,
                          checked, varname=field.varnames[1])
    return [filew, _(field.remlabel), resetw]

def renderJSDateField( rdr, field, renctx ):
    varname = field.varnames[0]
    fargs = (varname, renctx.rvalue and ", '%s'" % renctx.rvalue or '')
    script = (u"DateInput('%s', true, 'YYYYMMDD'%s);") % fargs

    # We must be able to accept both the string version and the datetime
    # version because of the different paths of argument parsing... it's
    # possible that we get asked to render something using values that have
    # not been parsed previously (for example, during the automated form
    # parsing errors).
    noscript = INPUT(name=varname, value=renctx.rvalue or '')

    return rdr._script(field, renctx, script, noscript)


#-------------------------------------------------------------------------------
# Register rendering routines.
HoutFormRenderer_routines = ((StringField, renderStringField),
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
                             (JSDateField, renderJSDateField),
                             (DateMenuField, renderMenuField),)

for fcls, fun in HoutFormRenderer_routines:
    atocha.render.register_render_routine(HoutFormRenderer, fcls, fun)



#-------------------------------------------------------------------------------
#
class HoutDisplayRenderer(HoutRenderer, atocha.render.DisplayRendererBase):
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
        HoutRenderer.__init__(self, *args, **kwds)

    def do_render( self, fields, action, submit ):
        # We only need return the table.
        return self.do_render_table(fields)

    def do_render_container( self, action_url ):
        return None

    def do_render_table( self, fields, css_class=None ):
        return self.do_render_display_table(fields, css_class=css_class)

    def do_render_submit( self, submit, reset ):
        return None

    def do_render_scripts( self ):
        return None

    #---------------------------------------------------------------------------

    def renderHidden( rdr, field, rvalue ):
        return None

#-------------------------------------------------------------------------------
#
def displayValue( rdr, field, renctx ):
    return [renctx.rvalue]

def displayTextAreaField( rdr, field, renctx ):
    return [PRE(renctx.rvalue)]

def displayEmailField( rdr, field, renctx ):
    if renctx.rvalue:
        return [A(renctx.rvalue, href='mailto:%s' % renctx.rvalue)]
    return []

def displayURLField( rdr, field, renctx ):
    if renctx.rvalue:
        return [A(renctx.rvalue, href='%s' % renctx.rvalue)]
    return []

def displayFileUploadField( rdr, field, renctx ):
    # Never display a file upload. Don't even try.
    return []


#-------------------------------------------------------------------------------
# Register rendering routines.
HoutDisplayRenderer_routines = ((StringField, displayValue),
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
                                (JSDateField, displayValue),
                                (DateMenuField, displayValue),)


for fcls, fun in HoutDisplayRenderer_routines:
    atocha.render.register_render_routine(HoutDisplayRenderer, fcls, fun)

