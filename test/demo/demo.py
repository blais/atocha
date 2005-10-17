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
import sys
from os.path import *
projects_root = dirname(dirname(dirname(dirname(dirname(sys.argv[0])))))
import os, StringIO, base64, shelve

# htmlout imports.
sys.path.append(join(projects_root, 'htmlout', 'lib', 'python'))
try:
    from htmlout import *
except ImportError:
    pass # We won't be able to test the htmlout renderers.

# atocha imports.
sys.path.append(join(projects_root, 'atocha', 'lib', 'python'))
from atocha import *
from atocha.norms.ncgi import CGINormalizer


#-------------------------------------------------------------------------------
#
rtype = 'htmlout' # Renderer type for demo/tests: 'text' or 'htmlout'

#-------------------------------------------------------------------------------
#
# Definition of test form.
#
form1 = Form(
    'test-form',

    # Normal unicode string.
    StringField('name', N_("Person's name")),

    # Ascii string.
    StringField('postal', N_("Postal code"), encoding='ascii'),

    # Hidden field.
    StringField('secret', hidden=1, initial='zanzibar',
                encoding='latin-1'),

    # Password field.
    PasswordField('passwd', N_("Password"), size=12, maxlen=8),

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
    FileUploadField('donation', N_('Donation (Send File)')),

    # A file that can be sent or reset.
    SetFileField('photo', N_('Photograph')),

    # Agree checkbox.
    AgreeField('terms', N_("Agree to Terms"),),

    action='handle.cgi', reset=1)


#-------------------------------------------------------------------------------
# Parser setup.
#
# Here we define a function that will get used by the FormParser class whenever
# it needs to perform a redirect. Form data, errors and message are meant to be
# passed to the routine where we're redirecting to.
#
# This needs only be setup once for the whole application, and is necessary to
# insure that Atocha not make assumptions about your web application framework.
# If you don't define the redirection mechanism, you can check the return value
# of FormParser.end() and do the redirect by hand, but you need to be careful
# not to forget to check everytimeq if you do that.

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

if 'HoutFormRenderer' in globals():
    HoutFormRenderer.scriptsdir = 'scripts'


#-------------------------------------------------------------------------------
# HTML page templates for our test scripts

template_pre = """Content-type: text/html

<html>
  <meta>
    <link href="style.css" rel="stylesheet" type="text/css"/>
    %(scripts)s
  </meta>
<body>

<div id="project-header">
  <a href="/"><img src="/home/project-header.png" id="logo"></a>
  <div id="project-home"><a href="/atocha">Project Home</a></div>
</div>

<h1 class="title">atocha demo: %(title)s</h1>
%(uimsg)s
<div class="document">
<div id="test-form">

"""

sourcelink = join('%s.txt' % splitext(basename(sys.argv[0]))[0])
template_post = """
</div>

<center>
<div id="source">
<a href="demo.txt" class="button">View Source Code</a>
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

#-------------------------------------------------------------------------------
#
def handle_query( args ):
    """
    CGI handler for rendering a query form to allow the user to enter input.
    """

    # Get old form data to fill the initial values of the form.
    db = getdb()
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

    # Create a form renderert to render the form..
    if rtype == 'text':
        r = TextFormRenderer(form1, values, errors,
                             output_encoding='latin-1')
        rendered = r.render(action='handle.cgi')
        scripts = r.render_scripts()
    else:
        from htmlout import tostring
        r = HoutFormRenderer(form1, values, errors)
        rendered = tostring(r.render(action='handle.cgi'), encoding='latin-1')
        scripts = [tostring(x, encoding='latin-1') for x in r.render_scripts()]
        scripts = '\n'.join(scripts)

    # Render the page (see template in other module).
    uimsg = message and '<div id="message">%s</div>' % message or ''
    sys.stdout.write(template_pre % {'title': 'Form Render and Handling',
                                     'uimsg': uimsg,
                                     'scripts': scripts})

    # Here, we use the form render:
    sys.stdout.write(rendered)
    sys.stdout.write(template_post)

#-------------------------------------------------------------------------------
#
def handler_handle( args ):
    """
    Handler for form submission.
    """
    
    cargs = cgi.FieldStorage()
    
    p = FormParser(form1, cargs, 'query.cgi')
    
    if 'merengue' in (p['dances'] or []):
        repldances = list(p['dances'])
        repldances.remove('merengue')
        p.error(u'Please fix error in dances below. I thought you were cuban.',
                dances=(u'No dominican dances here, please.', repldances))
    
    p.end()
    
    # Set final data in database and remove session data.
    db = getdb()
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
    
    
    # On success, redirect to render page.  You could decide to display results
    # from here.
    print 'Location: %s' % 'display.cgi'
    print
    print '302 Success.'
    sys.exit(0)
    
#-------------------------------------------------------------------------------
#
def handler_display( args ):
    """
    Render page for final accepted displayed data.
    Render with display renderer, with a text rendition at the bottom.
    """
    # Get data from database.
    db = getdb()
    values = db.get('data-%s' % form1.name, {})
    photo = db.get('photo-%s' % form1.name, None)
    photofn = db.get('photofn-%s' % form1.name, '')

    # Create display renderer to display the data.
    if rtype == 'text':
        r = TextDisplayRenderer(form1, values or {}, incomplete=1,
                                show_hidden=1,
                                output_encoding='latin-1')
        contents = r.render()

        if photo:
            contents += r.table(
                [(_(form1['photo'].label),
                  u'<img src="data:image/jpg;base64,%s"<br/>%s' %
                  (base64.b64encode(photo), photofn))] )
    else:
        r = HoutDisplayRenderer(form1, values or {}, incomplete=1,
                                show_hidden=1)
        form = r.render()
        contents = tostring(form, encoding='latin-1')

        if photo:
            htmlphoto = [
                IMG(src="data:image/jpg;base64,%s" % base64.b64encode(photo)),
                BR(), photofn or u'']
            contents += tostring(r.table( [(_(form1['photo'].label), htmlphoto)] ),
                                 encoding='latin-1')

    s = StringIO.StringIO()
    print >> s, '<div id="buttons">'
    print >> s, '<a href="query.cgi" id="edit" class="button">EDIT VALUES</a>'
    print >> s, '<a href="reset.cgi" id="edit" class="button">RESET</a>'
    print >> s, '</div>'

    print >> s, '</div>'
    print >> s, '<div>'
    print >> s, '<h2>Repr of Parsed Accepted Values</h2>'
    print >> s, '<pre id="values-repr">'
    for name, value in values.iteritems():
        print >> s, '%s: %s' % (name, repr(value))
    print >> s, '</pre>'
    contents += s.getvalue()

    # Set form data for edit.
    sys.stdout.write(template_pre % {'title': 'Form Display',
                                     'uimsg': '',
                                     'scripts': ''})
    sys.stdout.write(contents)
    sys.stdout.write(template_post)


#-------------------------------------------------------------------------------
#
def handler_reset( args ):
    """
    Handler that resets the form data stored in the local DB.
    """

    # Set form data for edit.
    db = getdb()
    for n in 'data', 'photo', 'photofn', 'session':
        try:
            del db['%s-%s' % (n, form1.name)]
        except Exception:
            pass

    handler_display(args)
