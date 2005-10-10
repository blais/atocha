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
    # Get form data.
    sdata = SessionData()
    sdata.setformdata(form1.name, values, errors, message)

    print 'Location: %s' % url
    print
    print '302 Errors in user input.'
    sys.exit(0)

# Setup automatic redirection mechanism.
FormParser.redirect_func = staticmethod(do_redirect)

# Setup normalizer for CGI scripts using Python's cgi module.
FormParser.normalizer = CGINormalizer()


#-------------------------------------------------------------------------------
#
class SessionData:
    """
    Simulate getting session data for the given form.

    We don't bother with cookies or form-specific storage for session
    data, since this is just a test and we will work locally.
    """
    def __init__( self ):
        fn = '/tmp/atocha-test-session-data.db'
        self.shelf = shelve.open(fn, 'c')

    def getformdata( self, formname ):
        try:
            values, errors, msg = self.shelf[formname]
        except KeyError:
            values, errors, msg = None, None, None
        return values, errors, msg

    def setformdata( self, formname, values, errors=None, msg=None ):
        self.shelf[formname] = values, errors, msg


#-------------------------------------------------------------------------------
#
template_pre = """Content-type: text/html

<html>
  <meta>
    <style type="text/css"/><!--

.formerror { color: red; font-size: smaller; }

.formtable {
  margin-left: auto;
  margin-right: auto;
}

td.formlabel {
  padding-left: 1em;
  padding-right: 1em;
  background-color: #F4F4F8;
}

div#message {
  background-color: #FCC;
  border: medium solid red;
  padding: 5px;
  margin: 5px;
}

div#contents {
  text-align: center;
  width: 800px;
  margin-left: auto;
  margin-right: auto;
  background-color: #FAFDFA;
}

pre#values-repr {
  background-color: white;
  border: thin dashed black;
  padding: 1em;
  text-align: left;
}

span.formreq {
  padding-left: 5px;
  padding-right: 5px;
  color: green;
}

--></style>
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
             StringField('name', N_("Person's name")),
             StringField('secret_code', N_("Secret code"), encoding='ascii'),
             TextAreaField('description', N_("Description"), rows=10, cols=60),
             DateField('birthday', N_("Birthday")),
             EmailField('email', N_("Email")),
             URLField('homepage', N_("Home Page")),
             IntField('number', N_("Age")),
             FloatField('height', N_("Height"), format='%.7f'),
             BoolField('confirm', N_("Are you sure?"),),
             RadioField('sex', [('m', N_('Male')),
                                ('f', N_('Female')),
                                ('x', N_('Maybe'))], N_('Sex'), orient=ORI_HORIZONTAL),
             action='handle.cgi')

##     'RadioField', 'MenuField', 'CheckboxesField', 'ListboxField',
##     'JSDateField',
##     'FileUploadField',

