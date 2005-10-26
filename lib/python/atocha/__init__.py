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

# Note: we declare those before due to cycle.
#-------------------------------------------------------------------------------
#
class AtochaError(Exception):
    """
    Class used for errors due to the misuse of the Atocha API.  An occurrence of
    this exception means that you most likely have made a mistake in your code
    using Atocha.
    """
    
#-------------------------------------------------------------------------------
#
class AtochaInternalError(AtochaError):
    """
    Internal errors probably due to a bug in the Atocha library.
    Please report such errors to the bug database at SourceForge.

    These exception may also occur due to bad code in 3rd party fields and/or
    renderers.
    """


# atocha imports.
from form import *
from field import *
from fields import *
from messages import *
from parse import *
from render import *
from norm import *

# Renderers.
# Note: we don't import the htmlout renderer automatically.
from renderers.rtext import *

