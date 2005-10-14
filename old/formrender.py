#!/usr/bin/env python
#
# $Source: /home/blais/repos/cvsroot/hume/app/lib/hume/formrender.py,v $
# $Id: formrender.py,v 1.39 2005/05/30 20:57:29 blais Exp $
#

"""
Renderer for forms using htmlout.
"""

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

# stdlib imports
import os.path
import datetime

# hume imports
from form import *
from htmlout import *


#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

deferror = N_('Error')

# Alters the behaviour of the error marking.
# This is experimental.
_wrap_errors = False

#-------------------------------------------------------------------------------
#
class NoDef:
    """Dummy class used for a non-specified optional parameter."""
    pass

#-------------------------------------------------------------------------------
#
class HtmloutRenderer(BaseRenderer):
    """
    Renderer that builds a tree of HTML nodes using the htmlout library.

    This renders input forms.
    """

    validstyles = [None, 'vertical', 'horizontal']

    def renderform( self, form, tr=None, action=None ):
        if tr is None: tr = _

        # the form itself
        formhtml = FORM(
            {'method': form.method, 'action': action or form.action,
             'name': form.name},
            )
        if form.encoding:
            formhtml.attrib['accept-charset'] = form.encoding

        for field in form.fields():
            if isinstance(field, FileUploadField):
                formhtml.attrib['enctype'] = 'multipart/form-data'
                break
        return formhtml

    def rendersubmit( self, form, tr=None, submit=None ):
        if tr is None: tr = _

        if isinstance(form.submit, str):
            inputs = [ INPUT(type='submit',
                             value=(submit or tr(form.submit)),
                             CLASS='submit-button') ]
        else:
            inputs = []
            for name, value in form.submit:
                inputs.append(INPUT(type='submit', CLASS='submit-button',
                                    name=name, value=tr(value) ))

        return CENTER(inputs)

    def renderfield( self, field, values=None, tr=None ):
        """See base class."""
        if tr is None: tr = _

        inputs = BaseRenderer.renderfield(self, field, values, tr)

        # set class on input
        if inputs and not field.ishidden():
            assert type(inputs) is types.ListType
            for input_ in inputs:
                input_.attrib.setdefault('class', '')
                input_.attrib['class'] += ' %s' % field.class_

        return inputs

    def rendertable( self, form, values=None, tr=None,
                     style=None, fields=None ):
        """
        Render the form, filling in the values that are present with the
        contents of the 'values' mapping (for example, as can be extracted with
        the cgi module).
        """

        assert style in self.validstyles
        if tr is None: tr = _

        elements = {}

        # table with fields
        table = TABLE(CLASS='form-table')
        if style == 'horizontal':
            tr1, tr2 = TR(parent=table), TR(parent=table)
        hidden_fields = []

        # FIXME: you need to make the fields render in the order that is
        # given. Right now they will render in the order that they're defined in
        # the form.
            
        for field in form.fields():
            if fields != None and field.name not in fields:
                continue
            inputs = self.renderfield(field, values, tr)
            elements[field.name] = inputs

            if inputs is None:
                continue

            if not field.ishidden():
                label = tr(field.label).strip()
                if not label.endswith(':'):
                    label += ':'

                tdlabel = TD(label, CLASS='form-label')
                tdinput = TD(inputs, CLASS='form-input')

                if style == 'vertical':
                    table.append( TR(tdlabel), TR(tdinput) )
                elif style == 'horizontal':
                    # Note: errmark label here?
                    tr1.append(tdlabel)
                    tr2.append(tdinput)
                else:
                    table.append( TR(tdlabel, tdinput) )
            else:
                for inpu in inputs:
                    inpu.attrib['type'] = 'hidden'
                    inpu.text = None
                hidden_fields.extend(inputs)

        # store a per-field index to the rendered fields
        table.rfields = elements

        return table, hidden_fields

    def rendertable_empty( self, label=None, inputs=None, style=None ):
        """
        Render an empty table, returning a tuple of (table, label container and
        inputs container), with the same HTML structure as for rendertable().
        """
        return self._rendertable_empty('form', label, inputs, style)
        
    @staticmethod
    def _rendertable_empty( pfx, label=None, inputs=None, style=None ):
        """
        Internal implementation of the empty table rendering method.
        """
        # table with fields
        table = TABLE(CLASS='%s-table' % pfx)
        if style == 'horizontal':
            tr1, tr2 = TR(parent=table), TR(parent=table)
        hidden_fields = []
        
        tdlabel = TD(CLASS='%s-label' % pfx)
        tdinput = TD(CLASS='%s-input' % pfx)

        if label:
            tdlabel.append(label + ':')
        if inputs:
            tdinput.append(inputs)
            
        if style == 'vertical':
            table.append( TR(tdlabel), TR(tdinput) )
        elif style == 'horizontal':
            # Note: errmark label here?
            tr1.append(tdlabel)
            tr2.append(tdinput)
        else:
            table.append( TR(tdlabel, tdinput) )

        return table, tdlabel, tdinput

    def rendererrors( self, htmlform, errors, tr=None ):
        """
        Add appropriate errors in the form.
        """
        if not errors:
            return

        assert type(errors) is types.DictType
        if tr is None: tr = _

        def errorvisitor( node, parent ):
            # Add a little span that contains an appropriate error message.
            if isinstance(node, INPUT) or \
                   isinstance(node, SELECT) or \
                   isinstance(node, TEXTAREA) or \
                   isinstance(node, SCRIPT):
                try:
                    name = node.attrib['name']
                    if name not in errors:
                        return True

                    idx = parent.children.index(node)
                    try:
                        errormsg = errors[name]
                        if not isinstance(errormsg, types.StringTypes):
                            errormsg = tr(deferror)
                    except KeyError:
                        errormsg = tr(deferror)

                    if _wrap_errors:
                        # Replace the child by a span which contains it.
                        del parent.children[idx]
                        parent.insert(idx,
                                      DIV('* ' + errormsg, BR(), node,
                                           CLASS='error-container'))
                    else:
                        # If the parent is a TD cell, set special class on it.
                        span_classes = 'error'
                        if isinstance(parent, TD):
                            parent.add_class('error-container')
                        else:
                            span_classes += ' error-container'

                        # insert SPAN and BR
                        parent.insert(idx,
                                      SPAN('* ' + errormsg, CLASS=span_classes))
                        if parent.__class__ is TD:
                            parent.insert(idx+1, BR())


                    # remove the error so that it only shows above the first
                    # widget with the given name
                    del errors[name]

                    # if there are no more errors, stop the traversal
                    if not errors:
                        return False
                except KeyError:
                    pass

            return True

        htmlform.visit(errorvisitor)

    def render( self, form, values=None, errors=None, tr=None,
                style=None, fields=None, action=None, submit=None ):

        htmlform = self.renderform(form, tr, action)
        table, hidden = \
               self.rendertable(form, values, tr, style, fields)
        htmlform.append(table, hidden)
        htmlform.append( self.rendersubmit(form, tr, submit) )

        if errors:
            self.rendererrors(htmlform, errors)

        # div container
        div = DIV(htmlform, id=form.name, CLASS='formblock')
        div.rfields = table.rfields
        return div

    #---------------------------------------------------------------------------

    def renderhidden( self, field, value, tr ):
        if value is None: value = ''

        inputs = []
        if type(value) in types.StringTypes:
            inputs.append(INPUT(name=field.name, type="hidden", value=value))
        elif type(value) is types.ListType:
            for val in value:
                inputs.append(INPUT(name=field.name, type="hidden", value=val))
        elif type(value) is types.BooleanType:
            inputs.append(INPUT(name=field.name, type="hidden",
                                value=value and '1' or '0'))
        else:
            raise RuntimeError
        return inputs

    def render_Field( self, field, value, tr, type_='text', checked=NoDef ):
        inpu = INPUT(name=field.name, type=type_, CLASS='form-input')
        if checked is not NoDef and checked:
            inpu.attrib['checked'] = 'checked'
        if value:
            inpu.attrib['value'] = value
        return [inpu]

    def render_TextField( self, field, value, tr, type_ ):
        inputs = self.render_Field(field, value, tr, type_)
        if field.maxlen:
            slen = str(field.maxlen)
            for inp in inputs:
                inp.attrib['maxlength'] = slen
        return inputs

    def render_StringField( self, field, value, tr ):
        return self.render_TextField(field, value, tr, 'text')

    def render_PasswordField( self, field, value, tr ):
        return self.render_TextField(field, value, tr, 'password')

    def render_TextAreaField( self, field, value, tr ):
        # Note: we cannot specify a maximum length for TEXTAREA.
        inpu = TEXTAREA(value or '', name=field.name)

        if field.rows:
            inpu.attrib['rows'] = str(field.rows)
        if field.cols:
            inpu.attrib['cols'] = str(field.cols)

        return [inpu]

    def render_IntField( self, field, value, tr ):
        return self.render_Field(field, value, tr, 'text')

    def render_FloatField( self, field, value, tr ):
        return self.render_Field(field, value, tr, 'text')

    def render_BoolField( self, field, value, tr ):
        return self.render_Field(field, '1', tr, 'checkbox', checked=value)

    def render_MultipleField( self, field, value, tr, type_ ):
        inputs = []
        for fvalue, flabel in field.values:
            inpu = INPUT(flabel, name=field.name, type=type_)
            inputs.append(inpu)

            if value:
                inpu.attrib['value'] = fvalue

            if type(value) is types.ListType:
                if fvalue in value:
                    inpu.attrib['checked'] = 'checked'

            elif fvalue == value:
                inpu.attrib['checked'] = 'checked'
        return inputs

    def render_RadioField( self, field, value, tr ):
## FIXME TODO add support for minitables like listfield below
        return self.render_MultipleField(field, value, tr, 'radio')

    def render_ListField( self, field, value, tr ):
        def getinpu( fvalue, flabel ):
            inpu = INPUT(name=field.name, type='checkbox', value=fvalue)
            if type(value) is types.ListType:
                if fvalue in value:
                    inpu.attrib['checked'] = 'checked'

            elif fvalue == value:
                inpu.attrib['checked'] = 'checked'
            return inpu

        if field.minitable == 'vertical':
            table = TABLE(CLASS='minitable')
            for fvalue, flabel in field.values:
                inpu = getinpu(fvalue, flabel)
                table.append(TR(TD(LABEL(flabel)), TD(inpu)))
            return [table]
        elif field.minitable == 'horizontal':
            tr1, tr2 = TR(), TR()
            table = TABLE(tr1, tr2, CLASS='minitable')
            for fvalue, flabel in field.values:
                inpu = getinpu(fvalue, flabel)
                tr1.append(TD(LABEL(flabel)))
                tr2.append(TD(inpu))
            return [table]
        else:
            return self.render_MultipleField(field, value, tr, 'checkbox')

    def render_MenuField( self, field, value, tr ):
        options = []
        for fvalue, flabel in field.values:
            option = OPTION(flabel, value=fvalue)
            options.append(option)

            if type(value) is types.ListType:
                if fvalue in value:
                    option.attrib['selected'] = 'selected'
            elif fvalue == value:
                option.attrib['selected'] = 'selected'

        select = SELECT(options, name=field.name)
        if field.multiple:
            select.attrib['multiple'] = 'multiple'
        if field.size:
            select.attrib['size'] = '1'

        return [select]

    def render_DateField( self, field, value, tr ):
        return self.render_Field(field, value, tr, 'text')

    def render_ActiveDateField( self, field, value, tr ):
        # Warning: the renderer of the form has the responsibility for adding
        # the script URL.
        vstr = ''
        if value:
            # We must be able to accept both the string version and the datetime
            # version because of the different paths of argument parsing... it's
            # possible that we get asked to render something using values that
            # have not been parsed previously (for example, during the automated
            # form parsing errors).
            if type(value) is datetime.date:
                vstr = value.strftime('%Y%m%d')
            elif isinstance(value, str):
                vstr = value
            else:
                raise ValueError(
                    "Incorrect value type given to active date field.")

        return [
            SCRIPT(
            "DateInput('%s', true, 'YYYYMMDD', %s);" % \
               (field.name, (vstr and "'%s'" % vstr) or 'undefined'),
            "hideInputs(this);",
            name=field.name),

            # hidden version, for use by tests only.
            NOSCRIPT(INPUT(name=field.name, value=vstr))
            ]
        # Note: setting 'name' on a SCRIPT tag is not standard, but it allows us
        # to render the errors later on.

    def render_FileUploadField( self, field, value, tr ):
        return self.render_Field(field, value, tr, 'file')

    def renderscripts( self, form, scriptsdir='' ):
        """
        Render the appropriate tags needed for the fields that the given form
        contains.
        """
        scripts = {}
        for fi in form.fields():
            if isinstance(fi, ActiveDateField) and 'active-date' not in scripts:
                scripts['active-date'] = SCRIPT(
                    ActiveDateField.notice,
                    type="text/javascript", language="JavaScript",
                    src=os.path.join(scriptsdir, ActiveDateField.filename))
                scripts['hide-inputs'] = SCRIPT(
                    type="text/javascript", language="JavaScript",
                    src=os.path.join(scriptsdir, 'hideInputs.js'))

        return scripts.values()


#-------------------------------------------------------------------------------
#
class HtmloutDisplayRenderer(BaseRenderer):
    """
    Renderer that builds a tree of HTML nodes using the htmlout library.

    This renders displays for input forms (no inputs), as table name/value
    pairs.
    """

    validstyles = [None]

    def render( self, form, values=None, tr=None, errors=None,
                style=None, noempty=False, fields=None ):
        """
        Render the form, filling in the values that are present with the
        contents of the 'values' mapping (for example, as can be extracted with
        the cgi module).

        'errors' is ignored.
        """

        if fields:
            assert type(fields) in [types.ListType, types.TupleType]
        assert style in self.validstyles
        if tr is None:
            tr = _

        # table with fields
        table = TABLE(CLASS='disp-table')
        hidden_fields = []
        for inputs, field in self.renderfields(form, values, tr,
                                               noempty, fields):
            if not field.ishidden():
                label = tr(field.label)
                if not label.endswith(':'):
                    label += ':'

                if style == 'vertical':
                    table.append( TR(TD(label, CLASS='disp-label')),
                                  TR(TD(inputs, CLASS='disp-value')) )
                else:
                    table.append( TR( TD(label, CLASS='disp-label'),
                                      TD(inputs, CLASS='disp-value') ) )
            else:
                hidden_fields.extend(inputs)

        return table

    def rendertable_empty( self, label=None, inputs=None, style=None ):
        """
        Render an empty display table.
        """
        return HtmloutRenderer._rendertable_empty(
            'disp', label, inputs, style)

    def renderhidden( self, field, value, tr ):
        # Note: we do not render the hidden fields at this point.
        # This could become an option in the future.
        return []

    def render_Field( self, field, value, tr, type_='text' ):
        return value

    def render_PasswordField( self, field, value, tr ):
        if value != None:
            return '*' * len(value)
        return None

    def render_EmailField( self, field, value, tr, type_='text' ):
        return A(value, href='mailto:%s' % value)

    def render_MultipleField( self, field, value, tr ):
        selected = []
        for fvalue, flabel in field.values:
            if type(value) is types.ListType:
                if fvalue in value:
                    selected.append(flabel)
            elif fvalue == value:
                selected.append(flabel)
        return ', '.join(selected)

    def render_FileUploadField( self, field, value, tr ):
        ## FIXME what do we do here now?
        return self.render_Field(field, value, tr, 'file')

    def render_ActiveDateField( self, field, value, tr ):
        vstr = ''
        if value:
            # We must be able to accept both the string version and the datetime
            # version because of the different paths of argument parsing... it's
            # possible that we get asked to render something using values that
            # have not been parsed previously (for example, during the automated
            # form parsing errors).
            if type(value) is datetime.date:
                vstr = value.strftime('%Y-%m-%d')
            elif isinstance(value, str):
                vstr = value
            else:
                raise ValueError(
                    "Incorrect value type given to active date field.")

        return self.render_Field(field, vstr, tr)

#-------------------------------------------------------------------------------
#
# Globals

formrdr = HtmloutRenderer()
formdisp = HtmloutDisplayRenderer()



#===============================================================================
# TEST
#===============================================================================

# Note: minimal tests, this library has actually been used during development
# and therefore much more tested than this.  I should really complete the tests
# here at some point.

import unittest
from form import TestFields

#-------------------------------------------------------------------------------
#
def suite():
    suite = unittest.makeSuite(TestFields)
    return suite

#-------------------------------------------------------------------------------
#
if __name__ == '__main__':
    import __builtin__, StringIO
    __builtin__.__dict__['_'] = tr_noop
    unittest.main()

