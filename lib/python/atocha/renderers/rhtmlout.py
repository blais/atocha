#!/usr/bin/env python
#
# $Id$
#

"""
Renderer for forms using htmlout.
"""

# stdlib imports.
import StringIO, codecs, types
from os.path import join

# atocha imports.
from atocha.render import FormRenderer
from atocha.fields import ORI_VERTICAL, FileUploadField
from atocha.messages import msg_type

# htmlout imports.
try:
    from htmlout import *
except ImportError:
    raise SystemExit(
        'Error: You need to install the htmlout library to use this module.')


__all__ = ['HoutFormRenderer']



#-------------------------------------------------------------------------------
#
class HoutRenderer(FormRenderer):
    """
    Base class for all renderers that will output to htmlout.
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
            assert isinstance(inputs, list)

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
    css_input = u'forminput'
    css_required = u'formreq'
    css_vertical = u'formminitable'
    
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
                ('action', form.action),
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
                    label = [label, SPAN(CLASS=self.css_required)]
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

        if isinstance(rvalue, unicode):
            inputs.append(
                INPUT(name=field.name, type="hidden", value=rvalue))
        elif isinstance(rvalue, list):
            for rval in rvalue:
                inputs.append(
                    INPUT(name=field.name, type="hidden", value=rval))
        else:
            raise RuntimeError("Error: unexpected type '%s' for rendering." %
                               type(rvalue))

        return inputs


    def _input( self, htmltype, field, value, checked=False, label=None ):
        """
        Render an html input.
        """
        inpu = INPUT(name=field.name, type=htmltype, value=value or u'',
                      CLASS=field.css_class)

        if label is not None:
            inpu.text = label
        if checked:
            inpu.attrib['checked'] = '1'            
        return inpu

    def _single( self, htmltype, field, value, errmsg,
                 checked=False, label=None ):
        """
        Render a single field.
        Returns a list.
        """
        return self._geterror(errmsg) + \
               [self._input(htmltype, field, value, checked, label)]

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
        text = TEXTAREA(rvalue, name=field.name, CLASS=field.css_class)
        if field.rows:
            text.attrib['rows'] = str(field.rows)
        if field.cols:
            text.attrib['cols'] = str(field.cols)
        return [self._geterror(errmsg), text]

    def renderPasswordField( self, field, rvalue, errmsg, required ):
        return self._single('text', field, rvalue, errmsg)

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
        return [self._geterror(errmsg)] + output

    def _renderMenu( self, field, rvalue, errmsg, required,
                     multiple=None, size=None ):
        "Render a SELECT menu. 'rvalue' is expected to be a list of values."

        select = SELECT(name=field.name, CLASS=field.css_class)
        if size is not None and size > 1:
            select.attrib['size'] = str(field.size)
        if multiple:
            select.attrib['multiple'] = '1'

        for vname, label in field.values:
            option = OPTION(_(label), value=vname)
            if vname in rvalue:
                option.attrib['selected'] = "selected"
            select.append(option)
        return [self._geterror(errmsg), select]

    def renderMenuField( self, field, rvalue, errmsg, required ):
        return self._renderMenu(field, [rvalue], errmsg, required)

    def renderCheckboxesField( self, field, rvalue, errmsg, required ):
        inputs = []
        for vname, label in field.values:
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

    def _script( self, field, errmsg, script, noscript=None ):
        "Render a script widget."
        # Note: setting 'name' on a SCRIPT tag is not standard, but it allows us
        # to render the errors later on.
        lines = [ SCRIPT(script, name=field.name, CLASS=field.css_class) ]
        if noscript:
            lines.append( NOSCRIPT(noscript, CLASS=field.css_class) )
        return [self._geterror(errmsg)] + lines

    def renderJSDateField( self, field, rvalue, errmsg, required ):
        fargs = (field.name, rvalue and ", '%s'" % rvalue or '')
        script = (u"DateInput('%s', true, 'YYYYMMDD'%s);"
                  u"hideInputs(this);") % fargs

        # We must be able to accept both the string version and the datetime
        # version because of the different paths of argument parsing... it's
        # possible that we get asked to render something using values that have
        # not been parsed previously (for example, during the automated form
        # parsing errors).
        noscript = INPUT(name=field.name, value=rvalue or '')

        return self._script(field, errmsg, script, noscript)



## FIXME: complete this, this is not complete yet.



# #-------------------------------------------------------------------------------
# #
# class HtmloutRenderer(BaseRenderer):
#     """
#     Renderer that builds a tree of HTML nodes using the htmlout library.
# 
#     This renders input forms.
#     """
# 
# # FIXME: this determines the style of tables... could we put this option
# # somewhere else?
#     validstyles = [None, 'vertical', 'horizontal']
# 
#     def renderform( self, form, action=None ):
#         # the form itself
#         formhtml = FORM(
#             {'method': form.method, 'action': action or form.action,
#              'name': form.name},
#             )
#         if form.encoding:
#             formhtml.attrib['accept-charset'] = form.encoding
# 
#         for field in form.fields():
#             if isinstance(field, FileUploadField):
#                 formhtml.attrib['enctype'] = 'multipart/form-data'
#                 break
#         return formhtml
# 
#     def rendersubmit( self, form, submit=None ):
#         if isinstance(form.submit, str):
#             inputs = [ INPUT(type='submit',
#                              value=(submit or _(form.submit)),
#                              CLASS='submit-button') ]
#         else:
#             inputs = []
#             for name, value in form.submit:
#                 inputs.append(INPUT(type='submit', CLASS='submit-button',
#                                     name=name, value=_(value) ))
# 
#         return CENTER(inputs)
# 
#     def renderfield( self, field, values=None ):
#         """See base class."""
#         inputs = BaseRenderer.renderfield(self, field, values)
# 
#         # set class on input
#         if inputs and not field.ishidden():
#             assert type(inputs) is types.ListType
#             for input_ in inputs:
#                 input_.add_class(field.css_class)
# 
#         return inputs
# 
#     def rendertable( self, form, values=None,
#                      style=None, fields=None ):
#         """
#         Render the form, filling in the values that are present with the
#         contents of the 'values' mapping (for example, as can be extracted with
#         the cgi module).
#         """
# 
#         assert style in self.validstyles
#         elements = {}
# 
#         # table with fields
#         table = TABLE(CLASS='form-table')
#         if style == 'horizontal':
#             tr1, tr2 = TR(parent=table), TR(parent=table)
#         hidden_fields = []
# 
#         # FIXME: you need to make the fields render in the order that is
#         # given. Right now they will render in the order that they're defined in
#         # the form.
# 
#         for field in form.fields():
#             if fields is not None and field.name not in fields:
#                 continue
#             inputs = self.renderfield(field, values)
#             elements[field.name] = inputs
# 
#             if inputs is None:
#                 continue
# 
#             if not field.ishidden():
#                 label = _(field.label).strip()
#                 if not label.endswith(':'):
#                     label += ':'
# 
#                 tdlabel = TD(label, CLASS='form-label')
#                 tdinput = TD(inputs, CLASS='form-input')
# 
#                 if style == 'vertical':
#                     table.append( TR(tdlabel), TR(tdinput) )
#                 elif style == 'horizontal':
#                     # Note: errmark label here?
#                     tr1.append(tdlabel)
#                     tr2.append(tdinput)
#                 else:
#                     table.append( TR(tdlabel, tdinput) )
#             else:
#                 for inpu in inputs:
#                     inpu.attrib['type'] = 'hidden'
#                     inpu.text = None
#                 hidden_fields.extend(inputs)
# 
#         # store a per-field index to the rendered fields
#         table.rfields = elements
# 
#         return table, hidden_fields
# 
#     def rendertable_empty( self, label=None, inputs=None, style=None ):
#         """
#         Render an empty table, returning a tuple of (table, label container and
#         inputs container), with the same HTML structure as for rendertable().
#         """
#         return self._rendertable_empty('form', label, inputs, style)
# 
#     @staticmethod
#     def _rendertable_empty( pfx, label=None, inputs=None, style=None ):
#         """
#         Internal implementation of the empty table rendering method.
#         """
#         # table with fields
#         table = TABLE(CLASS='%s-table' % pfx)
#         if style == 'horizontal':
#             tr1, tr2 = TR(parent=table), TR(parent=table)
#         hidden_fields = []
# 
#         tdlabel = TD(CLASS='%s-label' % pfx)
#         tdinput = TD(CLASS='%s-input' % pfx)
# 
#         if label:
#             tdlabel.append(label + ':')
#         if inputs:
#             tdinput.append(inputs)
# 
#         if style == 'vertical':
#             table.append( TR(tdlabel), TR(tdinput) )
#         elif style == 'horizontal':
#             # Note: errmark label here?
#             tr1.append(tdlabel)
#             tr2.append(tdinput)
#         else:
#             table.append( TR(tdlabel, tdinput) )
# 
#         return table, tdlabel, tdinput
# 
#     def rendererrors( self, htmlform, errors ):
#         """
#         Add appropriate errors in the form.
#         """
#         if not errors:
#             return
# 
#         assert type(errors) is types.DictType
# # FIXME: move this to a generic function with mention of being legacy.
#         def errorvisitor( node, parent ):
#             # Add a little span that contains an appropriate error message.
#             if isinstance(node, INPUT) or \
#                    isinstance(node, SELECT) or \
#                    isinstance(node, TEXTAREA) or \
#                    isinstance(node, SCRIPT):
#                 try:
#                     name = node.attrib['name']
#                     if name not in errors:
#                         return True
# 
#                     idx = parent.children.index(node)
#                     try:
#                         errormsg = errors[name]
#                         if not isinstance(errormsg, types.StringTypes):
#                             errormsg = _(deferror)
#                     except KeyError:
#                         errormsg = _(deferror)
# 
#                     if _wrap_errors:
#                         # Replace the child by a span which contains it.
#                         del parent.children[idx]
#                         parent.insert(idx,
#                                       DIV('* ' + errormsg, BR(), node,
#                                            CLASS='error-container'))
#                     else:
#                         # If the parent is a TD cell, set special class on it.
#                         span_classes = 'error'
#                         if isinstance(parent, TD):
#                             parent.add_class('error-container')
#                         else:
#                             span_classes += ' error-container'
# 
#                         # insert SPAN and BR
#                         parent.insert(idx,
#                                       SPAN('* ' + errormsg, CLASS=span_classes))
#                         if parent.__class__ is TD:
#                             parent.insert(idx+1, BR())
# 
# 
#                     # remove the error so that it only shows above the first
#                     # field with the given name
#                     del errors[name]
# 
#                     # if there are no more errors, stop the traversal
#                     if not errors:
#                         return False
#                 except KeyError:
#                     pass
# 
#             return True
# 
#         htmlform.visit(errorvisitor)
# 
#     def render( self, form, values=None, errors=None,
#                 style=None, fields=None, action=None, submit=None ):
# 
#         htmlform = self.renderform(form, action)
#         table, hidden = \
#                self.rendertable(form, values, style, fields)
#         htmlform.append(table, hidden)
#         htmlform.append( self.rendersubmit(form, submit) )
# 
#         if errors:
#             self.rendererrors(htmlform, errors)
# 
#         # div container
#         div = DIV(htmlform, id=form.name, CLASS='formblock')
#         div.rfields = table.rfields
#         return div
# 
# 
# 
#     #---------------------------------------------------------------------------
# 
#     def renderhidden( self, field, value ):
#         if value is None: value = ''
# 
#         inputs = []
#         if type(value) in types.StringTypes:
#             inputs.append(INPUT(name=field.name, type="hidden", value=value))
#         elif type(value) is types.ListType:
#             for val in value:
#                 inputs.append(INPUT(name=field.name, type="hidden", value=val))
#         elif type(value) is types.BooleanType:
#             inputs.append(INPUT(name=field.name, type="hidden",
#                                 value=value and '1' or '0'))
#         else:
#             raise RuntimeError
#         return inputs
# 
#     def render_Field( self, field, value, type_='text', checked=NoDef ):
#         inpu = INPUT(name=field.name, type=type_, CLASS='form-input')
#         if checked is not NoDef and checked:
#             inpu.attrib['checked'] = 'checked'
#         if value:
#             inpu.attrib['value'] = value
#         return [inpu]
# 
#     def render_TextField( self, field, value, type_ ):
#         inputs = self.render_Field(field, value, type_)
#         if field.maxlen:
#             slen = str(field.maxlen)
#             for inp in inputs:
#                 inp.attrib['maxlength'] = slen
#         return inputs
# 
#     def render_StringField( self, field, value ):
#         return self.render_TextField(field, value, 'text')
# 
#     def render_PasswordField( self, field, value ):
#         return self.render_TextField(field, value, 'password')
# 
#     def render_TextAreaField( self, field, value ):
#         # Note: we cannot specify a maximum length for TEXTAREA.
#         inpu = TEXTAREA(value or '', name=field.name)
# 
#         if field.rows:
#             inpu.attrib['rows'] = str(field.rows)
#         if field.cols:
#             inpu.attrib['cols'] = str(field.cols)
# 
#         return [inpu]
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
#         inputs = []
#         for fvalue, flabel in field.values:
#             inpu = INPUT(flabel, name=field.name, type=type_)
#             inputs.append(inpu)
# 
#             if value:
#                 inpu.attrib['value'] = fvalue
# 
#             if type(value) is types.ListType:
#                 if fvalue in value:
#                     inpu.attrib['checked'] = 'checked'
# 
#             elif fvalue == value:
#                 inpu.attrib['checked'] = 'checked'
#         return inputs
# 
#     def render_RadioField( self, field, value ):
# ## FIXME TODO add support for minitables like listfield below
#         return self.render_MultipleField(field, value, 'radio')
# 
#     def render_ListField( self, field, value ):
#         def getinpu( fvalue, flabel ):
#             inpu = INPUT(name=field.name, type='checkbox', value=fvalue)
#             if type(value) is types.ListType:
#                 if fvalue in value:
#                     inpu.attrib['checked'] = 'checked'
# 
#             elif fvalue == value:
#                 inpu.attrib['checked'] = 'checked'
#             return inpu
# 
#         if field.minitable == 'vertical':
#             table = TABLE(CLASS='minitable')
#             for fvalue, flabel in field.values:
#                 inpu = getinpu(fvalue, flabel)
#                 table.append(TR(TD(LABEL(flabel)), TD(inpu)))
#             return [table]
#         elif field.minitable == 'horizontal':
#             tr1, tr2 = TR(), TR()
#             table = TABLE(tr1, tr2, CLASS='minitable')
#             for fvalue, flabel in field.values:
#                 inpu = getinpu(fvalue, flabel)
#                 tr1.append(TD(LABEL(flabel)))
#                 tr2.append(TD(inpu))
#             return [table]
#         else:
#             return self.render_MultipleField(field, value, 'checkbox')
# 
#     def render_MenuField( self, field, value ):
#         options = []
#         for fvalue, flabel in field.values:
#             option = OPTION(flabel, value=fvalue)
#             options.append(option)
# 
#             if type(value) is types.ListType:
#                 if fvalue in value:
#                     option.attrib['selected'] = 'selected'
#             elif fvalue == value:
#                 option.attrib['selected'] = 'selected'
# 
#         select = SELECT(options, name=field.name)
#         if field.multiple:
#             select.attrib['multiple'] = 'multiple'
#         if field.size:
#             select.attrib['size'] = '1'
# 
#         return [select]
# 
#     def render_DateField( self, field, value ):
#         return self.render_Field(field, value, 'text')
# 
#     def render_ActiveDateField( self, field, value ):
#         # Warning: the renderer of the form has the responsibility for adding
#         # the script URL.
#         vstr = ''
#         if value:
#             # We must be able to accept both the string version and the datetime
#             # version because of the different paths of argument parsing... it's
#             # possible that we get asked to render something using values that
#             # have not been parsed previously (for example, during the automated
#             # form parsing errors).
#             if type(value) is datetime.date:
#                 vstr = value.strftime('%Y%m%d')
#             elif isinstance(value, str):
#                 vstr = value
#             else:
#                 raise ValueError(
#                     "Incorrect value type given to active date field.")
# 
#         return [
#             SCRIPT(
#             "DateInput('%s', true, 'YYYYMMDD', %s);" % \
#                (field.name, (vstr and "'%s'" % vstr) or 'undefined'),
#             "hideInputs(this);",
#             name=field.name),
# 
#             # hidden version, for use by tests only.
#             NOSCRIPT(INPUT(name=field.name, value=vstr))
#             ]
#         # Note: setting 'name' on a SCRIPT tag is not standard, but it allows us
#         # to render the errors later on.
# 
#     def render_FileUploadField( self, field, value ):
#         return self.render_Field(field, value, 'file')
# 
#     def renderscripts( self, form, scriptsdir='' ):
#         """
#         Render the appropriate tags needed for the fields that the given form
#         contains.
#         """
#         scripts = {}
#         for fi in form.fields():
#             if isinstance(fi, ActiveDateField) and 'active-date' not in scripts:
#                 scripts['active-date'] = SCRIPT(
#                     ActiveDateField.script_notice,
#                     type="text/javascript", language="JavaScript",
#                     src=os.path.join(scriptsdir, ActiveDateField.script))
#                 scripts['hide-inputs'] = SCRIPT(
#                     type="text/javascript", language="JavaScript",
#                     src=os.path.join(scriptsdir, 'hideInputs.js'))
# 
#         return scripts.values()
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# # FIXME: remove 'noempty' everywhere, it isn't used much apart from the profile
# # and cannot be guaranteed to make sense anymore.  We are better work around it
# # in the client code.
# 
# # This is actually not quite right: in the display renderer, it does make sense
# # to not want to render fields for which there is no value set.  It only makes
# # sense for the display-only renderer.  Maybe that renderer could take an option
# # in its constructor?
# 
# 
# #-------------------------------------------------------------------------------
# #
# class HtmloutDisplayRenderer(BaseRenderer):
#     """
#     Renderer that builds a tree of HTML nodes using the htmlout library.
# 
#     This renders displays for input forms (no inputs), as table name/value
#     pairs.
#     """
# 
#     validstyles = [None]
# 
#     def render( self, form, values=None, errors=None,
#                 style=None, noempty=False, fields=None ):
#         """
#         Render the form, filling in the values that are present with the
#         contents of the 'values' mapping (for example, as can be extracted with
#         the cgi module).
# 
#         'errors' is ignored.
#         """
# 
#         if fields:
#             assert type(fields) in [types.ListType, types.TupleType]
#         assert style in self.validstyles
# 
#         # table with fields
#         table = TABLE(CLASS='disp-table')
#         hidden_fields = []
#         for inputs, field in self.renderfields(form, values,
#                                                noempty, fields):
#             if not field.ishidden():
#                 label = _(field.label)
#                 if not label.endswith(':'):
#                     label += ':'
# 
#                 if style == 'vertical':
#                     table.append( TR(TD(label, CLASS='disp-label')),
#                                   TR(TD(inputs, CLASS='disp-value')) )
#                 else:
#                     table.append( TR( TD(label, CLASS='disp-label'),
#                                       TD(inputs, CLASS='disp-value') ) )
#             else:
#                 hidden_fields.extend(inputs)
# 
#         return table
# 
#     def rendertable_empty( self, label=None, inputs=None, style=None ):
#         """
#         Render an empty display table.
#         """
#         return HtmloutRenderer._rendertable_empty(
#             'disp', label, inputs, style)
# 
#     def renderhidden( self, field, value ):
#         # Note: we do not render the hidden fields at this point.
#         # This could become an option in the future.
#         return []
# 
#     def render_Field( self, field, value, type_='text' ):
#         return value
# 
#     def render_PasswordField( self, field, value ):
#         if value != None:
#             return '*' * len(value)
#         return None
# 
#     def render_EmailField( self, field, value, type_='text' ):
#         return A(value, href='mailto:%s' % value)
# 
#     def render_MultipleField( self, field, value ):
#         selected = []
#         for fvalue, flabel in field.values:
#             if type(value) is types.ListType:
#                 if fvalue in value:
#                     selected.append(flabel)
#             elif fvalue == value:
#                 selected.append(flabel)
#         return ', '.join(selected)
# 
#     def render_FileUploadField( self, field, value ):
#         ## FIXME what do we do here now?
#         return self.render_Field(field, value, 'file')
# 
#     def render_ActiveDateField( self, field, value ):
#         vstr = ''
#         if value:
#             # We must be able to accept both the string version and the datetime
#             # version because of the different paths of argument parsing... it's
#             # possible that we get asked to render something using values that
#             # have not been parsed previously (for example, during the automated
#             # form parsing errors).
#             if type(value) is datetime.date:
#                 vstr = value.strftime('%Y-%m-%d')
#             elif isinstance(value, str):
#                 vstr = value
#             else:
#                 raise ValueError(
#                     "Incorrect value type given to active date field.")
# 
#         return self.render_Field(field, vstr)
# 
# 
# 
# ## FIXME: remove
# ## # Use messages.py instead
# ## deferror = N_('Error')
# 
# ## # Alters the behaviour of the error marking.
# ## # This is experimental.
# ## _wrap_errors = False
