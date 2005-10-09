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

# atocha imports.
import fields
import messages # To make sure that the _() function is setup.


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
        self._form = form
        "The form instance that we're rendering."

        self._values = values
        """A dict of the values to fill the field with.  Values do not have to
        be present for all the fields in the form.  The types of the values
        should match the corresponding data types of the fields."""

        self._errors = errors
        """A dict of the previous errors to render. The keys should correspond
        to the names of the fields."""

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
        if not self._incomplete and self._form.names() != self._rendered:
            # This gets ignored to some extent, because it is called within the
            # destructor, and only outputs a message to stderr, but it should be
            # ugly enough in the program's logs to show up.
            raise RuntimeError(
                "Error: Form renderer did not render form completely.")

    def _render_field( self, field, hide=None ):
        """
        Render a single field (implementation).

        This method dispatches between the visible and hidden field rendering,
        fetches the appropriate value for the field, and checks the basic
        assumptions that are made in the framework.

        If 'hide' is specified, we force the rendering of this field as if it
        was a hidden field, with the same conditions.
        """
        assert isinstance(field, fields.Field)

        # Figure out if this field should be rendered as hidden or not.
        hidden = hide or field.ishidden()
        
        #
        # Get value to be used to render the field.
        #
        if self._values is None or field.name not in self._values:
            dvalue = None # Not set.
        else:
            try:
                # Note: this assignment may result in dvalue being None, which
                # is the same as if not set.
                dvalue = self._values[field.name]
            except KeyError:
                dvalue = None # Not set.
            
        if dvalue is None:
            # If the field is hidden and the value is not set, we raise an
            # error. We should not be able to render hidden fields without a
            # value, and we will not use the initial value for hidden fields.
            # Hidden fields should have an explicit value provided in the
            # 'values' array.
            if hidden:
                raise RuntimeError(
                    "Error: Hidden field '%s' has no value." % field.name)

            # Otherwise we use the initial value for rendering.
            dvalue = field.initial

        # Convert the data value into a value suitable for rendering.
        #
        # This should never fail, the fields should always be able to convert
        # the data values from the all the types that they declare into a
        # rendereable value type.
        if dvalue is not None:
            assert isinstance(dvalue, field.types_data)
            rvalue = field.render_value(dvalue)

            if not isinstance(rvalue, field.types_render):
                raise RuntimeError(
                    "Error: rvalue '%s' is invalid (expecting %s)." %
                    (repr(rvalue), repr(field.types_render)))
        else:
            rvalue = None

        #
        # Get error to be used for rendering.
        #
        if self._errors is not None:
            try:
                error = self._errors[field.name]
            except KeyError:
                # An error of None signals there is no error.
                error = None
        else:
            error = None

        #
        # Dispatch to the appropriate method for rendering the fields.
        #
        renderobj = self
        if hidden:
            # Make sure that we're not trying to render hidden fields that have
            # errors associated to them.
            if error is not None:
                raise RuntimeError(
                    "Error: Hidden field '%s' must have no errors." %
                    field.name)

            output = renderobj.renderHidden(field, rvalue)
        else:
            # Dispatch to function with name renderXXX() on type field, for
            # example, renderStringField().  Your derived class must have
            # methods func_<type>.  A search is NOT made up the inheritance
            # tree, on purpose, because we want to force the renderer to make an
            # explicit decision about how to render all the widget types used in
            # the form.
            mname = 'render%s' % field.__class__.__name__
            try:
                method = getattr(renderobj, mname)
                output = method(field, rvalue, error, field.isrequired())
            except AttributeError:
                raise RuntimeError(
                    "Error: No method on renderer to handle field '%s'." %
                    field)

        # Return output from the field-specific rendering code.
        return output

    #---------------------------------------------------------------------------
    # Public methods that you can use.

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

        The arguments support both the only/ignore syntax, as well as specifying
        the names of the fields directly as strings. See the documentation for
        method Form.select_fields() for the meaning of the 'only' and 'ignore'
        arguments.
        """
        for fname in fieldnames:
            assert isinstance(fname, str)

        # Process only/ignore field selection.
        only = fieldnames + kwds.get('only', [])
        ignore = kwds.get('ignore', None)
        fields = self._form.select_fields(only, ignore)

        # Render the table given the fields.
        return self.do_render_table(fields)

    def table( self, label=None, inputs=None ):
        """
        User-callable method for do_table().
        """
        return self.do_table(label, inputs)

    def render_field( self, fieldname, hide=None ):
        """
        Render a single field.

        This method dispatches between the visible and hidden field rendering,
        fetches the appropriate value for the field, and checks the basic
        assumptions that are made in the framework.
        """
        try:
            field = self._form[fieldname]
        except KeyError:
            raise RuntimeError("Error: invalid field name.")

        return self._render_field(field, hide)

    def render_submit( self, submit=None ):
        """
        Renders the submit buttons. 

        An alternate set of submit buttons from the ones that is in the form can
        be specified.
        """
        return self.do_render_submit(submit or self._form.submit)


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
        
    def do_render_table( self, fields ):
        """
        Render a table of (label, inputs) pairs, for convenient display.  The
        types of the return values depends on the renderer.  Hidden fields are
        normally rendered outside of a table, returned just after the table.
        See the documentation for the particular renderer for details.

        This is the implementation of the render_table() method.
        """
        raise NotImplementedError
        
    def do_table( self, label=None, inputs=None ):
        """
        Renders a simplistic table, inserting the given label and inputs.  The
        inputs and return values depend on the renderer.  The render_table()
        method is expected to reuse this in its implementation, and it is
        convenient to provide such a method for really custom rendering as well.

        This method assumes that the field is visible and has some kind of
        label.  You should therefore avoid using the method to render hidden
        fields.

        Note: the label is assumed to not have been translated yet.
        """
        raise NotImplementedError

    def do_render_submit( self, submit ):
        """
        This abstract method must be provided by all the derived classes, to
        implement the actual rendering algorithm for the form container.
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

    def renderField( self, field, rvalue, error, required ):
        """
        Example of the signature for the methods that must be overriden.
        """
        raise RuntimeError("Do not call this.")

