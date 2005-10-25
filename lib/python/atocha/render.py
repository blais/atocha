#!/usr/bin/env python
#
# $Id$
#

"""
Renderer for forms and their fields.

The forms and their definitions can be used not just to parse and validate the
submitted values, but also to render the necessary bits of HTML to display the
widgets.

This module contains the simple text output classes.  See the other module for
rendering to a tree of elements which gets flattenned out later.
"""

# stdlib imports
import sys
if sys.version_info[:2] < (2, 4):
    from sets import Set as set
import types

# atocha imports.
from atocha import AtochaError, AtochaInternalError
from atocha.form import Form
from field import Field
import fields
from atocha.fields.uploads import FileUploadField
from messages import msg_type, msg_registry # Used for _() setup.
from parse import FormParser


__all__ = ['FormRenderer']


#-------------------------------------------------------------------------------
#
class FormRenderer:
    """
    Form renderer base class.

    This class is instantiated to oversee the process of rendering a specific
    form, given certain initial values to fill the widgets with.  It can also
    check to make sure that all the fields in a form have been renderer before
    it gets deleted.
    """
    def __init__( self, form, values=None, errors=None, incomplete=False ):
        assert form is not None
        self._form = form
        "The form instance that we're rendering."

        self._values = values
        """A dict of the values to fill the field with.  Values do not have to
        be present for all the fields in the form.  The types of the values
        should match the corresponding data types of the fields."""

        self._errors = errors
        """A dict of the previous errors to render. The keys should correspond
        to the names of the fields, and the values are either bools, strings or
        error tuples (message, replacement_rvalue)."""

        self._incomplete = incomplete
        """Whether we allow the rendering to be an incomplete set of the form's
        fields."""

        self._rendered = set()
        """Set of field names that have already been rendered. This is used to
        make sure that all of a form's fields are rendered."""

    def __del__( self ):
        """
        Destructor override that just makes sure that we rendered all the fields
        of the given form before we got destroyed.
        """
        if not self._incomplete and set(self._form.names()) != self._rendered:
            # This gets ignored to some extent, because it is called within the
            # destructor, and only outputs a message to stderr, but it should be
            # ugly enough in the program's logs to show up.
            raise AtochaError(
                "Error: Form renderer did not render form completely.")

    def _render_field( self, field, state ):
        """
        Render a single field (implementation).

        This method dispatches between the visible and hidden field rendering
        states, fetches the appropriate value for the field, and checks the
        basic assumptions that are made in the framework.

        If 'state' is specified, we force the rendering of this field as if it
        was in that state, with the same conditions.  This is useful for hiding
        a field.
        """
        assert isinstance(field, Field)
        assert state in Field._states

        #
        # Get error to be used for rendering.
        #
        errmsg = None
        if self._errors is not None:
            try:
                error = self._errors[field.name]

                # Make sure that the error is a triple.
                error = FormParser._normalize_error(error)
                errmsg = error[0]
            except KeyError:
                # An error of None signals there is no error.
                error = None
        else:
            error = None

        #
        # Get value to be used to render the field.
        #
        dorender = True
        if self._values is None or field.name not in self._values:
            # There is no value for the field.

            # If the field is hidden/read-only/disabled and the value is not
            # set, we raise an error. We should not be able to render such
            # fields without a value.  Also, such fields should not have errors.
            # Such fields should have an explicit value provided in the 'values'
            # array.
            if state != Field.NORMAL and field.initial is None:
                raise AtochaError(
                    "Error: Hidden/read-only field '%s' has no value." %
                    field.name)

            # We will look at using the replacement value instead of the value.
            if error is not None:
                # If the values field is not present, use the replacement value.
                errmsg, repl_rvalue = error
                if repl_rvalue is None:
                    dvalue = None # Ask to render a value of None.
                else:
                    rvalue = repl_rvalue
                    dorender = False
            else:
                # The value is not present for the given field.  We use the
                # initial value.
                dvalue = field.initial
        else:
            # The value is present in the parsed values.

            # But if there is also a replacement value, use that over the parsed
            # value.  It is likely that the client code set an error on a
            # validly parsed value, due to custom validation code, and if he set
            # a replacement value, he indicates that he wants that to be used
            # instead of the parsed value.
            if error is not None:
                # If the values field is not present, use the replacement value.
                errmsg, repl_rvalue = error
                if repl_rvalue is not None:
                    rvalue = repl_rvalue
                    dorender = False

            # No replacement value was found, use the parsed valid value for
            # render.
            if dorender:
                dvalue = self._values[field.name]

        # Convert the data value into a value suitable for rendering.
        #
        # This should never fail, the fields should always be able to convert
        # the data values from the all the types that they declare into a
        # rendereable value type.
        if dorender:
            assert dvalue is None or isinstance(dvalue, field.types_data)
            rvalue = field.render_value(dvalue)

        if not isinstance(rvalue, field.types_render):
            raise AtochaError(
                "Error: rvalue '%s' is invalid (expecting %s)." %
                (repr(rvalue), repr(field.types_render)))

        # Dispatch to renderer.
        output = self._dispatch_render(field, rvalue, errmsg, state)

        # Mark this fields as having been rendered.
        self._rendered.add(field.name)

        # Return output from the field-specific rendering code.
        return output

    def _dispatch_render( self, field, rvalue, errmsg, state ):
        """
        Dispatch to the appropriate method for rendering the fields.
        """

        # The class is derived, so dispatch to this class. This might become
        # customizable in the future.
        renderer = self

        if state != Field.NORMAL:
            # Make sure that we're not trying to render
            # hidden/read-only/disabled fields that have errors associated to
            # them.
            if errmsg is not None:
                raise AtochaError(
                    "Error: Non-editabled field '%s' must have no errors." %
                    field.name)

        if state is Field.HIDDEN:
            output = renderer.renderHidden(field, rvalue)

        else:
            # Dispatch to function with name renderXXX() on type field, for
            # example, renderStringField().  Your derived class must have
            # methods render<type>.
            #
            # Note: we could use the visitor pattern but we would need to
            # customize all the field classes to support it.

            # Search the classes in order of inheritance.
            clsstack = [field.__class__]
            method = None
            while method is None:
                cls = clsstack.pop()
                mname = 'render%s' % cls.__name__
                method = getattr(renderer, mname, None)
                clsstack.extend(cls.__bases__)

            if method is None:
                raise AtochaInternalError(
                    "Error: renderer has no method for '%s'." %
                    field.__class__)

            renctx = RenderContext(state, rvalue, errmsg, field.isrequired())
            try:
                output = method(field, renctx)
            except Exception, e:
                raise
                raise AtochaInternalError(
                    "Error: While attempting to render field '%s': %s" %
                    (field, str(e)))

        return output

    def _get_label( self, field ):
        """
        Returns a printable label for the given field.
        """
        return (field.label and _(field.label)
                or field.name.capitalize().decode('ascii'))

    def validate_renderer( cls ):
        """
        Checks that all the required rendering methods are present in the
        renderer's implementation.  A rendering method should be provided for
        each of the field types, so that an explicit about what to do for each
        of them is made explicit.

        Note: this method is used by the test routines only, to verify that any
        implemented renderer is complete.
        """
        for att in fields.__all__:
            if not isinstance(getattr(fields, att), Field):
                continue
            try:
                getattr(cls, 'render%s' % att)
            except AttributeError:
                raise AtochaInternalError(
                    'Renderer %s does not have required method %s' % (cls, att))


        for att in  ('do_render', 'do_render_container', 'do_render_table',
                     'do_table', 'do_render_submit', 'do_render_scripts',
                     'renderHidden',):
            try:
                getattr(cls, att)
            except AttributeError:
                raise AtochaInternalError(
                    'Renderer %s does not have required method %s' % (cls, att))

    validate_renderer = classmethod(validate_renderer)


    #---------------------------------------------------------------------------
    # Public methods that you can use.

    def update_values( self, newvalues ):
        """
        Update the renderer's values with the new values.
        """
        self._values.update(newvalues)

    def render( self, only=None, ignore=None, action=None, submit=None ):
        """
        Render the entire form including the labels and inputs and hidden fields
        and all.  This is intended to be the simple straightforward way to
        render an reasonably looking form with no fuss.  If you want to
        customize rendering to make it more fancy, render the components of the
        form independently.

        :Arguments:

          See the documentation for method Form.select_fields() for the meaning
          of the 'only' and 'ignore' arguments.

        """
        fields = self._form.select_fields(only, ignore)
        return self.do_render(fields,
                              action or self._form.action,
                              submit or self._form.submit)

    def render_container( self, action=None ):
        """
        Renders the form prefix only.  There returned value should be the
        container tags for the form, which include the form's name, action,
        method and encoding.

        An alternate action from the one that is in the form can be specified.
        """
        return self.do_render_container(action or self._form.action)

    def render_table( self, *fieldnames, **kwds ):
        """
        Render a table of (label, inputs) pairs, for convenient display.  The
        types of the return values depends on the renderer.  Hidden fields are
        normally rendered outside of a table, returned just after the table.
        See the documentation for the particular renderer for details.

        Specify the field names as the normal arguments.

        :Keyword Arguments:

        - 'only' and 'ignore': See the documentation for method
          Form.select_fields() for the meaning of the 'only' and 'ignore'
          arguments.

        - 'css_class': can be used to add a custom CSS class to this table.

        """
        for fname in fieldnames:
            assert isinstance(fname, str)

        # Process only/ignore field selection.
        only = fieldnames
        if only in kwds:
            only = only + tuple(kwds.pop('only'))
        ignore = kwds.pop('ignore', None)
        fields = self._form.select_fields(only, ignore)

        # Render the table given the fields.
        css_class = kwds.pop('css_class', None)
        return self.do_render_table(fields, css_class=css_class)

    def table( self, pairs=(), css_class=None ):
        """
        User-callable method for rendering a simple table. 'pairs' is an
        iterable of (label, value) pairs.  'css_class' can be used to add a
        custom CSS class to this table.
        """
        return self.do_table(pairs, css_class=css_class)

    def render_field( self, fieldname, state=None ):
        """
        Render given field (by name).
        If you want to render multiple fields, use render_table().
        """
        try:
            field = self._form[fieldname]
        except KeyError, e:
            raise AtochaError(
                "Error: field not present in form: %s" % str(e))

        if state is None:
            state = field.state
        return self._render_field(field, state)

    def render_submit( self, submit=None ):
        """
        Renders the submit buttons.

        An alternate set of submit buttons from the ones that is in the form can
        be specified.
        """
        return self.do_render_submit(submit or self._form.submit,
                                     self._form.reset)

    def render_scripts( self ):
        """
        Renders the scripts to be added to the meta headers.
        """
        scripts = self._form.getscripts()
        return self.do_render_scripts(scripts)

    #---------------------------------------------------------------------------
    # Abstract methods that must get implemented by the derived class.
    # Normally the client should not call any of these directly.

    def do_render( self, fields, action=None, submit=None ):
        """
        This abstract method must be provided by all the derived classes, to
        implement the actual rendering algorithm on the given list of fields.
        """
        raise NotImplementedError

    def do_render_container( self, action ):
        """
        This abstract method must be provided by all the derived classes, to
        implement the actual rendering algorithm for the form container.
        """
        raise NotImplementedError

    def do_render_table( self, fields, css_class=None ):
        """
        Render a table of (label, inputs) pairs, for convenient display.  The
        types of the return values depends on the renderer.  Hidden fields are
        normally rendered outside of a table, returned just after the table.
        See the documentation for the particular renderer for details.

        This is the implementation of the render_table() method.
        """
        raise NotImplementedError

    def do_table( self, pairs=(), extra=None, css_class=None ):
        """
        Renders a simplistic table, inserting the given list of (label, inputs)
        pairs.  The return value type depend on the renderer.  The
        do_render_table() method is expected to reuse this in its
        implementation, and it is convenient to provide such a method for really
        custom rendering as well.

        This method assumes that the field is visible and has some kind of
        label.  You should therefore avoid using the method to render hidden
        fields.

        Note: the label is assumed to not have been translated yet.
        """
        raise NotImplementedError

    def do_render_submit( self, submit, reset ):
        """
        This abstract method must be provided by all the derived classes, to
        implement the actual rendering algorithm for the form container.
        """
        raise NotImplementedError

    def do_render_scripts( self, scripts ):
        """
        Renders the scripts to be added to the meta headers (implementation).
        """
        raise NotImplementedError

    def renderHidden( self, field, rvalue ):
        """
        You must override this method to render a hidden field.  Since all the
        hidden fields get rendered using very similar code, we don't impose a
        burden on the field-specific renderer methods to have to deal with
        rendering both normal and hidden fields.  Instead, each of the fields
        knows how to render itself to a value suitable for inclusion in a hidden
        input.
        """
        raise NotImplementedError

    def renderField( self, field, renctx ):
        """
        Example of the signature for the methods that must be overriden.
        See the class RenderContext for more details.

        Note that these rendering methods must support rendering normal,
        read-only and disabled fields.
        """
        raise AtochaError("Do not call this.")


    #-------------------------------------------------------------------------------
    #
    def render_buttons( cls, buttons, action, formname=None, method=None ):
        """
        Shorthand convenience function for rendering buttons.  This is a class
        method that should be invoked from an appropriate derived class.

        :Arguments:

        - 'cls': The renderer class that invokes this method.

        - 'action': The URL of the action to take upon button press.

        - 'buttons': See Form.submit for details.

        - 'formname': The name of the form to use (only important if you're
          going to have multiple button forms in the same page).

        - 'method': See Form.method for details.

        Note that if you can, if would be more efficient to create and keep a
        Form object between requests.
        """
        assert type(cls) is not FormRenderer and issubclass(cls, FormRenderer)

        # Create form to contain buttons.
        if formname is None:
            formname = 'form-buttons'
        if not buttons:
            raise AtochaError("You need to specify some buttons.")
        form = Form(formname, submit=buttons, action=action, method=method)

        # Create a renderer.
        rdr = cls(form)

        # Return rendered values.
        return rdr.render()

    render_buttons = classmethod(render_buttons)


#-------------------------------------------------------------------------------
#
class DisplayRendererBase:
    """
    Common options for display renderers (but they might not make sense for
    other renderer types, this is why we provide this special class).
    """

    def __init__( self, kwds ):
        if 'errors' in kwds:
            raise AtochaError("Errors not allowed in display renderer.")

        self.show_hidden = kwds.pop('show_hidden', True)
        """Determines whether we render the fields that are hidden."""

        self.show_unset = kwds.pop('show_unset', True)
        """Determines whether we render the fields that have no associated value
        to render.  This will display set but empty values (such as empty
        strings)."""

        self.show_empty = kwds.pop('show_empty', True)
        """Determines whether we render the fields that do have an associated
        value but which evaluates to False.  This will not display fields with
        empty strings."""

    def _display_field( self, field, dvalue ):
        """
        Convert the value for the given field from valid type data to a
        user-displayable string.  This is used by the display renderers to
        provide a nice user rendering of the values.

        This always returns a unicode string, ready to be printed.
        """
        assert isinstance(field, Field)
        assert isinstance(dvalue, field.types_data)

        # Have the value converted by the field for display.
        #
        # Note: if there is any translation to be done, we expect the
        # display_value method to have done it before us.  This is so that
        # combinations of translated values can be performed (e.g. see
        # CheckboxesField).
        uvalue = field.display_value(dvalue)

        # Dispatch to renderer. Notice we hard-wire no-errors and normal visible
        # states.
        output = self._dispatch_render(field, uvalue, None, Field.NORMAL)

        # Mark this fields as having been rendered.
        self._rendered.add(field.name)

        # Return output from the field-specific rendering code.
        return output

    def do_render_display_table( self, fields, css_class=None ):
        """
        Render a table for diplay, honoring the appropriate options.
        """
        visible = []
        for field in fields:
            # Don't display unset fields.
            if not self.show_unset and field.ishidden():
                continue

            # Never display a file upload. Don't even try.
            if isinstance(field, FileUploadField):
                continue

            # If there is an error for the field, return a constant error
            # string. We do not print replacement values for the display, the
            # value has to be fully valid.  It may be possible that displaying a
            # field with errors is not allowed in the code that calls this, but
            # this might change in the future.
            if self._errors is not None and field.name in self._errors:
                rendered = msg_registry['display-error']

            elif self._values is None:
                # Cull out unset values.
                if not self.show_unset:
                    continue
                else:
                    rendered = msg_registry['display-unset']

            else:
                # We might have a value available to convert and display.
                try:
                    dvalue = self._values[field.name]

                    # Cull out empty values.
                    if not self.show_empty and not dvalue:
                        continue

                    # Render the field to be displayed.
                    rendered = self._display_field(field, dvalue)

                except KeyError:
                    # Cull out unset values.
                    if not self.show_unset:
                        continue
                    else:
                        rendered = msg_registry['display-unset']

            visible.append( (self._get_label(field), rendered) )

        return self.do_table(visible, css_class=css_class)


#-------------------------------------------------------------------------------
#
class RenderContext:
    """
    Simply holds the context data that is used to render a field.
    Note that this is used for non-hidden fields only.
    """
    def __init__( self, state, rvalue, errmsg, required ):

        self.state = state
        "The final state to render the widgets in."

        self.rvalue = rvalue
        "The value to be rendered, already converted to a valid render type."

        self.errmsg = errmsg
        "The error message associated to this field."

        self.required = required
        """Whether this field is to be marked as required or not (typically
        adding a star next to the label).  Typically this is not used at all
        when rendering the actual input but specific renderers may wish to
        render the actual inputs differently if they are required."""

