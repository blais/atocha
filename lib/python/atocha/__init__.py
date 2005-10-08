#!/usr/bin/env python
#
# $Id$
#

"""
Server-side form handling library.

This is a library that provides classes for representing forms, that can then be
used for rendering the form, parsing and converting the types in the handler.

There are mainly four components:

1. Form class: container of fields, and global parameters for the entire form
   (submit buttons, actions, method, etc.);

2. Field classes: a hierarchy of classes that represent various types of
   inputs.  These are akin to widgets in a desktop UI toolkit;

3. FormRenderer: a class that knows how to render all the fields appropriately.
   There can be various implementations of this renderer, for example, one that
   renders directly to HTML text, or one that builds a tree of XHTML nodes.  You
   can also build a renderer class that renders not to a form, but to
   displayable values only;

4. FormParser: a helper class that supports the code patterns needed to handle
   forms and parse its arguments, and return and render appropriate error
   messages.

To understand this code, you should read the individual documentations of these
four components, they contain details which will allow you grasp a complete
picture of what this library offers.

For each field in a form, at various points the data that moves through them is
of three different types:

- the 'data' value type, which is the final Python type that we want to read;

- the 'render' value type, a type that is suitable for rendering purposes by
  renderer;

- the 'parse' value type, the type of data that is submitted by forms to a
  browser, to be parsed into the 'data' type.

We will refer to those as 'dvalue', 'rvalue' and 'pvalue' in the code, in order
to disambiguate the expected types of the variables.

Input Data
----------

We assume that the input data has been processed with mod_python.

(We could eventually adapt this library to support CGI scripts as well, if there
is time.)


Notes
-----

- This will only work with Python 2.3 and over.

- All user-printable strings are assumed to be of unicode types (str's are not
  supported and we tried to avoid implicit conversions--if we find implicit
  conversions, we will change the code to remove them).  This does not include
  the parsed values of the string fields, which may have specific encodings, and
  that will be stated explicitly.  Thus anything that the user may see will be
  automatically assumed to be of unicode type and we will assert on this
  wherever it makes sense.  This helps delinate what strings are used as
  internal values and what strings are really meant for rendering, and enforces
  consistency.

"""

# form imports.
from form_def import *
from form_fields import *
from form_messages import *
from form_parse import *
from form_render import *
from form_rtext import *
## from form_rhtmlout import *



# Stuff to do
# ===========
## FIXME: todo

# Progress:
# * form_rsimple.py
# * form_rhtmlout.py

# on the fields: maybe we have to add the following methods:
# - hidden_value( self, dvalue ) 
# - display_value( self, dvalue ) 

# - move the css styles for the table on the renderer classes themselves.  The
#   styles should be default'ed on the classes and looked up with 'self.' so
#   that it becomes possible to simply override those in derived classes.



# - We need to support a replacement value of the incorrect type for fields.




# Ideas
# =====
#
# Renderer
# --------
#
# Fields
# ------
#
#
# - Other widgets:
#
#    - Reset button, see Quixote for some examples.
#    - Agree button, bool checkbox that MUST be enabled by the user.
# 
# - Rendering radio buttons that have no default value currently initializes
#   without a selection (invalid to submit).
#
# - prepare_values() implementations may have to be different when the
#   field is a hidden type.  How do you deal with this?
#
# Parser
# ------
#
# - We could add a method in this object that will simply allow redirecting,
#   because this object always knows how to store the form data, form errors,
#   etc.
#
# - Maybe we could eventually provide a way to at least decode the args which
#   have no corresponding field in the form (if that never becomes necessary,
#   don't do so).
#






# Changes to adapt existing code with
# -----------------------------------
#
# default=  becomes  initial=
# notnull=  becomes  required=

# Field.prepare_value becomes render_value
# Field.parse becomes Field.parse_value
# Form.addField becomes Field.addfield

# Remove method calls on former FormError class:
#     def formerrors( self ):
#     def errlabels( self ):
#     def errnames( self ):
#     def errfields( self ):

# - Orientation for radio fields has become an int, change from 'minitable'.
#
# ActiveDateField become JSDateField

# ListField becomes CheckboxesField

# hidden fields now require an explicit 'hidden=1' option.





## form_parser: Needs a concrete implementation for hume:

## # FIXME: change this to use the errors to check if there are errors
##         if self._status:
##             if not self._messages:
##                 setStatus(self._status, self.__generic_message)
##             else:
##                 setStatus(self._status, '  '.join(self._messages))

##             if len(self):
##                 setFormData(self._form.name, self)
##             if self._errors:
##                 setFormErrors(self._form.name, self._errors)

