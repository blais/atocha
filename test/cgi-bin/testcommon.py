#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# $Id$
#

"""
Common definitions for CGI tests.

You might define something similar for your own environment.
"""

# stdlib imports.
import sys, shelve
from os.path import *

# atocha imports.
root = dirname(dirname(dirname(sys.argv[0])))
sys.path.append(join(root, 'lib', 'python'))
from atocha import *


#-------------------------------------------------------------------------------
# Parser setup
#
def do_redirect( url, form, status, message, values, errors ):
    # Store form data for later retrieval in session data.
    db = getdb()
    db['session-%s' % form1.name] = values, errors, message


    print 'Location: %s' % url
    print
    print '302 Errors in user input.'
    sys.exit(0)

# Setup automatic redirection mechanism.
FormParser.redirect_func = staticmethod(do_redirect)

# Setup normalizer for CGI scripts using Python's cgi module.
FormParser.normalizer = CGINormalizer()

# Setup form renderer for rendering scripts.
TextFormRenderer.scriptsdir = 'scripts'


#-------------------------------------------------------------------------------
#
def getdb():
    """
    Returns an open object with a dict interface to store data in a DB.
    This is used to store both the final data and the session form data.
    """
    fn = '/tmp/atocha-test-session-data.db'
    shelf = shelve.open(fn, 'c')
    return shelf


#-------------------------------------------------------------------------------
#
template_pre = """Content-type: text/html

<html>
  <meta>
    <link href="style.css" rel="stylesheet" type="text/css"/>
    %(scripts)s
  </meta>
<body>
<h1>%(title)s</h1>
%(uimsg)s
<div id="contents">
"""

template_post = """
</div>
</body>
</html>
"""
    
#-------------------------------------------------------------------------------
#
# Test form.
form1 = Form('test-form',

             # Normal unicode string.
             StringField('name', N_("Person's name")),

             # Ascii string.
             StringField('postal', N_("Postal code"), encoding='ascii'),

             # Hidden field.
             StringField('secret', hidden=1, initial='zanzibar',
                         encoding='latin-1'),

             # A text area.
             TextAreaField('description', N_("Description"), rows=10, cols=60),

             # Simple date.
             DateField('birthday', N_("Birthday")),

             # A fancier date input widget.
             JSDateField('barmitz', N_("Bar Mitzvah")),
             
             # Email address and URL fields.
             EmailField('email', N_("Email")),
             URLField('homepage', N_("Home Page")),

             # Numerical fields.
             IntField('number', N_("Age")),
             FloatField('height', N_("Height"), format='%.7f'),

             # Boolean checkbox.
             BoolField('veggie', N_("Vegetarian?"),),

             # Radio buttons.
             RadioField('sex', [('m', N_('Male')),
                                ('f', N_('Female')),
                                ('x', N_('Maybe'))],
                        N_('Sex'), orient=ORI_HORIZONTAL,
                        initial='x'),

             # A single-choice menu.
             MenuField('marital', [(1, N_('Single')),
                                   (2, N_('Married')),
                                   (3, N_('Divorced')),
                                   (0, N_('(Other...)'))],
                       N_('Marital Status'),
                       initial=3),

             # A list of options.
             CheckboxesField('dances', [('salsa', N_('Salsa')),
                                        ('tango', N_('Tango')),
                                        ('rumba', N_('Rumba')),
                                        ('chacha', N_('Cha-cha-chá')),
                                        ('merengue', N_('Merengue')),],
                             N_('Favourite Dances'),
                             initial=['rumba', 'salsa']),

             # A list of options (single).
             ListboxField('beer', [('heineken', N_('Heineken')),
                                   ('kro', N_('Kronenbourg')),
                                   ('corona', N_('Corona')),
                                   ('budweiser', N_('Budweiser')),
                                   ('paulaner', N_('Paulaner')),],
                          N_('The Best Beer, if any'),
                          ),

             # A list of options (multiple).
             ListboxField('yogas', [('ash', N_('Ashtanga')),
                                    ('iyen', N_('Iyengar')),
                                    ('kri', N_('Kripalu')),
                                    ('bik', N_('Bikram')),
                                    ('kun', N_('Kundalini'))],
                          N_('Yogas Practiced'),
                          initial=['ash', 'kun'], multiple=1
                          ),

             # A file that can be uploaded.
             FileUploadField('photo', N_('Photograph')),

             action='handle.cgi', reset=1)

