#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# $Id$
#

"""
Common definitions for demo and interactive tests.

You might define something similar for your own environment.  I admin that this
demo script is overly complex because I'm trying to showcase most of the basic
features of Atocha.  Your code could be much simpler.
"""

# stdlib imports
import sys, os, StringIO, base64, shelve
from os.path import *

# Current renderer type for demo/tests: 'text' or 'htmlout'.
rtype = 'htmlout'

# atocha imports
from atocha import *

# htmlout imports
if rtype == 'htmlout':
    try:
        from htmlout import *
        from atocha.renderers.rhtmlout import *
        rtype = 'htmlout'
    except ImportError:
        # We won't be able to test the htmlout renderers.
        print >> sys.stderr, ('Warning: htmlout not available, '
                              'falling back on text renderers.')
        rtype = 'text'


#-------------------------------------------------------------------------------
#
# Definition of test form.
#
form1 = Form(
    'test-form',

    # Normal unicode string.
    StringField('name', N_("Person's Name")),

    # Ascii string.
    StringField('postal', N_("Postal Code"), encoding='ascii'),

    # Hidden field.
    StringField('secret', state=Field.HIDDEN, initial='zanzibar',
                encoding='latin-1'),

    # Password field.
    PasswordField('passwd', N_("Password"), size=12, maxlen=8),

    # A text area.
    TextAreaField('description', N_("Description"),
                  rows=10, cols=60),

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
                 N_('The Best Beer (If Any)'),
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
    FileUploadField('donation', N_('Donation (Send File)')),

    # A file that can be sent or reset.
    SetFileField('photo', N_('Photograph')),

##     # Agree checkbox.
##     AgreeField('terms', N_("Agree to Terms"),),

    # Disabled field.
    StringField('veteran', N_("Veteran"), initial=u'Disabled...',
                state=Field.DISABLED),

    # Read-Only field.
    StringField('notouch', N_("Touch Me"), initial=u"Don't touch",
                state=Field.READONLY),

    action='handle', reset=1)


#-------------------------------------------------------------------------------
# HTML page templates for our test scripts

template_pre = """

<html>
  <meta>
    <link href="resources/style.css" rel="stylesheet" type="text/css"/>
    %(scripts)s
  </meta>
<body>

<div id="project-header">
  <a href="/"><img src="/home/furius-logo-w.png" id="logo"></a>
  <div id="project-home"><a href="/atocha">Project Home</a></div>
</div>

<h1 class="title">atocha demo: %(title)s</h1>
%(uimsg)s
<div class="document">
<div id="test-form">

"""

template_post = """
</div>

<center>
<div id="source">
<a href="demo.py.txt" class="button">View Source Code</a>
</div>
</center>

</div>

</body>
</html>
"""


#-------------------------------------------------------------------------------
#
def getdb():
    """
    Returns an open object with a dict interface to store data in a DB.
    This is used to store both the final data and the session form data.

    Normally you would be using a more decent session and data store, this is
    just for testing because it is easy and works everywhere.
    """
    fn = '/tmp/atocha-test-session-data.db'
    shelf = shelve.open(fn, 'c')
    return shelf

#===============================================================================
# HANDLERS
#===============================================================================

ext = None

#-------------------------------------------------------------------------------
#
def handler_query():
    """
    Handler for rendering a query form to allow the user to enter input.
    """
    db = getdb()

    # Get old form data to fill the initial values of the form.
    # Fetch the real data.
    values, errors, message = db.get('data-%s' % form1.name, {}), None, None

    # Fetch the session data.
    if 'session-%s' % form1.name in db:
        sessvalues, errors, message = db.get('session-%s' % form1.name,
                                             (None, None, None))
        # Remove that session data (we've used it).
        del db['session-%s' % form1.name]

        # Update session values with newly parsed values.
        if sessvalues:
            values.update(sessvalues)

    db.close()

    # Create a form renderert to render the form..
    if rtype == 'text':
        rdr = TextFormRenderer(form1, values, errors,
                             output_encoding='latin-1')
        rendered = rdr.render(action='handle' + ext)
        scripts = rdr.render_scripts()
    else:
        from htmlout import tostring
        rdr = HoutFormRenderer(form1, values, errors)
        rendered = tostring(rdr.render(action='handle' + ext), encoding='latin-1')
        scripts = [tostring(x, encoding='latin-1') for x in rdr.render_scripts()]
        scripts = '\n'.join(scripts)

    # Render the page (see template in other module).
    s = StringIO.StringIO()
    uimsg = ''
    if message:
        uimsg = '<div id="message">%s</div>' % message.encode('latin-1')
    s.write(template_pre % {'title': 'Form Render and Handling',
                            'uimsg': uimsg,
                            'scripts': scripts})

    # Here, we use the form render:
    s.write(rendered)
    s.write(template_post)

    return s.getvalue()

#-------------------------------------------------------------------------------
#
def handler_handle( args, url ):
    """
    Handler for form submission.
    """
    db = getdb()

    p = FormParser(form1, args, 'query' + ext)

    if 'merengue' in (p['dances'] or []):
        repldances = list(p['dances'])
        repldances.remove('merengue')
        p.error(u'Please fix error in dances below. I thought you were cuban.',
                dances=(u'No dominican dances here, please.', repldances))

    p.end()

    # Set final data in database and remove session data.
    values = p.getvalues(1)

    # Handle setfile upload.
    if p['photo'] is False:
        # Reset photo.
        db['photo-%s' % form1.name] = db['photofn-%s' % form1.name] = None

    elif p['photo']:
        # Read in photograph file, if there is one.
        db['photo-%s' % form1.name] = p['photo'].read()
        db['photofn-%s' % form1.name] = p['photo'].filename

    db['data-%s' % form1.name] = values
    db.close()

    return handler_display()

#-------------------------------------------------------------------------------
#
def handler_display():
    """
    Render page for final accepted displayed data.
    Render with display renderer, with a text rendition at the bottom.
    """
    db = getdb()

    # Get data from database.
    values = db.get('data-%s' % form1.name, {})
    photo = db.get('photo-%s' % form1.name, None)
    photofn = db.get('photofn-%s' % form1.name, '')
    db.close()

    # Create display renderer to display the data.
    if rtype == 'text':
        rdr = TextDisplayRenderer(form1, values or {}, incomplete=1,
                                show_hidden=1,
                                output_encoding='latin-1')
        contents = rdr.render()

        if photo and 'photo' in form1.names():
            contents += rdr.table(
                [(_(form1['photo'].label),
                  u'<img src="data:image/jpg;base64,%s"<br/>%s' %
                  (base64.b64encode(photo), photofn))] )
    else:
        rdr = HoutDisplayRenderer(form1, values or {}, incomplete=1,
                                  show_hidden=1)
        form = rdr.render()
        contents = tostring(form, encoding='latin-1')

        if photo and 'photo' in form1.names():
            htmlphoto = [
                IMG(src="data:image/jpg;base64,%s" % base64.b64encode(photo)),
                BR(), photofn or u'']
            contents += tostring(rdr.table( [(_(form1['photo'].label), htmlphoto)] ),
                                 encoding='latin-1')

    s = StringIO.StringIO()
    s.write(template_pre % {'title': 'Form Display',
                            'uimsg': '',
                            'scripts': ''})

    s.write(contents)
    print >> s, '<div id="buttons">'
    print >> s, '<a href="query%s" id="edit" class="button">EDIT VALUES</a>' % ext
    print >> s, '<a href="reset%s" id="edit" class="button">RESET</a>' % ext
    print >> s, '</div>'

    print >> s, '</div>'
    print >> s, '<div>'
    print >> s, '<h2>Repr of Parsed Accepted Values</h2>'
    print >> s, '<pre id="values-repr">'
    for name, value in values.iteritems():
        print >> s, '%s: %s' % (name, repr(value))
    print >> s, '</pre>'

    s.write(template_post)

    return s.getvalue()


#-------------------------------------------------------------------------------
#
def handler_reset():
    """
    Handler that resets the form data stored in the local DB.
    """
    db = getdb()

    # Set form data for edit.
    for n in 'data', 'photo', 'photofn', 'session':
        try:
            del db['%s-%s' % (n, form1.name)]
        except Exception:
            pass
    db.close()

    return handler_display()




#===============================================================================
# TEST FORM OVERRIDE
#===============================================================================

## form1 = Form(
##     'test-form',
##     # Normal unicode string.
##     StringField('name', N_("Person's name")),
##     # Ascii string.
##     StringField('postal', N_("Postal code"), encoding='ascii'),
##     action='handle', reset=1)

