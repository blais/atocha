#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# $Id$
#

"""
Tests for forms library.

Run these tests using the codespeak py.test tool.
"""

# stdlib imports.
import sys, os, datetime, StringIO, webbrowser

# form imports.
from atocha import *


#-------------------------------------------------------------------------------
#
class TestSimple:
    """
    Simple varied tests.
    """

    def test_simple1( self ):
        'Simple form test.'

        f = Form('test-form')
        f.addfield( StringField('name', N_('The Name')) )
        
        # Test very basic stuff.
        args = {'name': _u8str}
        p = FormParser(f)
        p.parse(args)
        assert p['name'] == u'école'


#-------------------------------------------------------------------------------
#
class TestForm:
    """
    Test form functionalities.
    """


#-------------------------------------------------------------------------------
#
_u8str = u'école'.encode('utf-8')

class TestFields:
    """
    Tests for specific fields.
    """

    def test_string( self ):
        'StringField tests.'

        # Test without a label.
        f = Form('test-form', StringField('name'))
        args = {'name': _u8str}
        p = FormParser(f)
        p.parse(args)
        assert p['name'] == u'école'

        # Test some encodings.
        f = Form('test-form',
                 StringField('nameuni', N_('The Name')),
                 StringField('nameutf', N_('The Name'), encoding='utf-8'),
                 StringField('namelatin', N_('The Name'), encoding='latin-1'),
                 StringField('nameascii', N_('The Name'), encoding='ascii'))

        # Test various encodings for the string field.
        args = {'nameuni': _u8str,
                'nameutf': _u8str,
                'namelatin': _u8str,
                'nameascii': 'ecole'}
        p = FormParser(f)
        p.parse(args)
        assert p['nameuni'] == u'\xe9cole' and type(p['nameuni']) is unicode
        assert p['nameutf'] == '\xc3\xa9cole' and type(p['nameutf']) is str
        assert p['namelatin'] == '\xe9cole' and type(p['namelatin']) is str
        assert p['nameascii'] == 'ecole' and type(p['nameascii']) is str
        assert not p.haserrors()

        # Test string encoding errors.
        args = {'nameascii': _u8str}
        p = FormParser(f)
        p.parse(args)
        assert p['nameascii'] == '?cole' and type(p['nameascii']) is str
        assert p.haserrors()
        assert p.geterrors().keys() == ['nameascii']

        # Test required field.
        f = Form('test-form', StringField('name', required=1))
        args = {}
        p = FormParser(f)
        p.parse(args)
        assert p.haserrors()
        assert p.geterrors().keys() == ['name']
        assert p['name'] is None

        # Test with multiline input.
        f = Form('test-form', StringField('name', minlen=4, maxlen=10))
        args = {'name': 'Martin\nblibli\nlis'}
        p = FormParser(f)
        p.parse(args)
        assert p.haserrors()

        # Test min/max lengths.
        f = Form('test-form', StringField('name', minlen=4, maxlen=10))
        args = {'name': 'Martin'}
        p = FormParser(f)
        p.parse(args)
        assert not p.haserrors()

        args = {'name': 'Jon'}
        p = FormParser(f)
        p.parse(args)
        assert p.haserrors()

        args = {'name': 'Elizabeth the 3rd'}
        p = FormParser(f)
        p.parse(args)
        assert p.haserrors()

        # Test strip option.
        f = Form('test-form', StringField('name', strip=1))
        args = {'name': ' Martin  '}
        p = FormParser(f)
        p.parse(args)
        assert not p.haserrors()
        assert p['name'] == 'Martin'

    def test_textarea( self ):
        'Textarea tests.'
        
        # Test strip option.
        f = Form('test-form', TextAreaField('quote', N_('Quote')))

        args = {'quote': u"""When I hear people complain about Lisp's parentheses,
        it sounds to my ears like someone saying: 'I tried one of those bananas,
        which you say are so delicious. The white part was ok, but the yellow
        part was very tough and tasted awful.'""".encode(f.encoding)}

        p = FormParser(f)
        p.parse(args)
        assert not p.haserrors()
        assert p['quote']
        

    def test_date( self ):
        'DateField tests.'

        # Test simple.
        f = Form('test-form', DateField('birthday'))

        p = FormParser(f)
        p.parse({})
        assert not p.haserrors() and p['birthday'] is None
        
        f = Form('test-form', DateField('birthday', required=1))

        p = FormParser(f)
        p.parse({})
        assert p.haserrors() and 'birthday' in p.geterrors()

        p = FormParser(f)
        p.parse({'birthday': '2005-10-03'})
        assert not p.haserrors() and p['birthday'] == datetime.date(2005, 10, 03)

        p = FormParser(f)
        p.parse({'birthday': 'Thu, Jan 01, 2005'})
        assert p.haserrors() and 'birthday' in p.geterrors()


    def test_email( self ):
        'EmailField tests.'

        f = Form('test-form', EmailField('email'))

        p = FormParser(f, args={'email': 'blais@furius.ca'})
        assert not p.haserrors() and p['email'] == 'blais@furius.ca'

        p = FormParser(f, args={'email': 'Martin Blais <blais@furius.ca>'})
        assert not p.haserrors() and p['email'] == 'blais@furius.ca'
        
        p = FormParser(f, args={'email': 'blais'})
        assert p.haserrors() and p.geterrorfields() == ['email']

        f2 = Form('test-form', EmailField('email', accept_local=1))
        p = FormParser(f2, args={'email': 'blais'})
        assert not p.haserrors() and p['email'] == 'blais'

        p = FormParser(f, args={'email': 'blais+bli@furius.ca'})
        assert not p.haserrors() and p['email'] == 'blais+bli@furius.ca'

        p = FormParser(f, args={'email': 'blais@furius.org'})
        assert not p.haserrors() and p['email'] == 'blais@furius.org'

        p = FormParser(f, args={'email': 'blais[@furius.com'})
        assert p.haserrors() and p['email'] == 'blais[@furius.com'

        # TLDs are not checked, it seems. We'll take it.
        # p = FormParser(f, args={'email': 'blais@furius.glu'})
        # assert p.haserrors() and p.geterrorfields() == ['email']

    def test_url( self ):
        'URLField tests.'

        ## FIXME: todo

    def test_int( self ):
        'IntField tests.'

        # Test simple.
        f = Form('test-form', IntField('number', minval=3, maxval=20))

        p = FormParser(f)
        p.parse({'number': '17'})
        assert not p.haserrors()
        assert p['number'] == 17

        p = FormParser(f)
        p.parse({'number': '2'})
        assert p.haserrors() and 'number' in p.geterrors()

        p = FormParser(f)
        p.parse({'number': '25'})
        assert p.haserrors() and 'number' in p.geterrors()

        p = FormParser(f)
        p.parse({'number': '17.3'})
        assert p.haserrors() and 'number' in p.geterrors()

        # Test required.
        f = Form('test-form', IntField('number', required=1))
        p = FormParser(f)
        p.parse({})
        assert p.haserrors() and 'number' in p.geterrors()

    def test_float( self ):
        'FloatField tests.'

        # Test simple.
        f = Form('test-form', FloatField('number', minval=3.2, maxval=20.7))

        p = FormParser(f)
        p.parse({'number': '17.3'})
        assert not p.haserrors()
        assert p['number'] == 17.3

        p = FormParser(f)
        p.parse({'number': '17'})
        assert not p.haserrors()
        assert p['number'] == 17

        p = FormParser(f)
        p.parse({'number': '2.03'})
        assert p.haserrors() and 'number' in p.geterrors()

        p = FormParser(f)
        p.parse({'number': '25.87'})
        assert p.haserrors() and 'number' in p.geterrors()

        # Test required.
        f = Form('test-form', IntField('number', required=1))
        p = FormParser(f)
        p.parse({})
        assert p.haserrors() and 'number' in p.geterrors()

    def test_bool( self ):
        'BoolField tests.'

        # Test simple.
        f = Form('test-form', BoolField('agree'))

        p = FormParser(f)
        p.parse({})
        assert not p.haserrors() and p['agree'] is False
        
        p = FormParser(f)
        p.parse({'agree': 'bullshyte'})
        assert not p.haserrors() and p['agree'] is True

        p = FormParser(f)
        p.parse({'agree': ''})
        assert not p.haserrors() and p['agree'] is False

    def _test_one( self, cls, **extra ):
        'One choices test.'

        # Simple tests.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'), **extra))

        p = FormParser(f)
        p.parse({})
        assert p.haserrors() and 'coffee' in p.geterrors()
        
        p = FormParser(f)
        p.parse({'coffee': 'latte'})
        assert not p.haserrors() and p['coffee'] == 'latte'

        p = FormParser(f)
        try:
            p.parse({'coffee': ['latte', 'expresso']})
            assert 0
        except RuntimeError: pass

        p = FormParser(f)
        try:
            p.parse({'coffee': 'american'})
            assert 0
        except RuntimeError: pass            


        # Test with labels.
        f = Form('test-form',
                 cls('coffee', [('latte', N_('Latte')),
                                ('expresso', N_('Expresso')),
                                ('moccha', N_('Moccha'))], **extra))

        p = FormParser(f)
        p.parse({'coffee': 'expresso'})
        assert not p.haserrors() and p['coffee'] == 'expresso'


        # Test with integer values.
        f = Form('test-form',
                 cls('coffee', [(10, N_('Latte')),
                                (20, N_('Expresso')),
                                (30, N_('Moccha'))], **extra))

        p = FormParser(f)
        p.parse({'coffee': '10'})
        assert not p.haserrors() and p['coffee'] == '10'


        # Test with disabled value check.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'),
                     nocheck=1, **extra))

        p = FormParser(f)
        p.parse({'coffee': 'american'})
        assert not p.haserrors() and p['coffee'] == 'american'


    def _test_many( self, cls, **extra ):
        'Many choices tests.'

        # Simple tests.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'), **extra))

        p = FormParser(f)
        p.parse({})
        assert not p.haserrors() and p['coffee'] == []
        
        p = FormParser(f)
        p.parse({'coffee': 'latte'})
        assert not p.haserrors() and p['coffee'] == ['latte']

        p = FormParser(f)
        p.parse({'coffee': ['latte', 'expresso']})
        assert not p.haserrors() and p['coffee'] == ['latte', 'expresso']

        p = FormParser(f)
        try:
            p.parse({'coffee': 'american'})
            assert 0
        except RuntimeError: pass            

        # Test with labels.
        f = Form('test-form',
                 cls('coffee', [('latte', N_('Latte')),
                                ('expresso', N_('Expresso')),
                                ('moccha', N_('Moccha'))], **extra))

        p = FormParser(f)
        p.parse({'coffee': 'expresso'})
        assert not p.haserrors() and p['coffee'] == ['expresso']


        # Test with integer values.
        f = Form('test-form',
                 cls('coffee', [(10, N_('Latte')),
                                (20, N_('Expresso')),
                                (30, N_('Moccha'))], **extra))

        p = FormParser(f)
        p.parse({'coffee': '10'})
        assert not p.haserrors() and p['coffee'] == ['10']


        # Test with disabled value check.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'),
                     nocheck=1, **extra))

        p = FormParser(f)
        p.parse({'coffee': 'american'})
        assert not p.haserrors() and p['coffee'] == ['american']


    def test_radio( self ):
        'RadioField tests.'

        self._test_one(RadioField)

    def test_menu( self ):
        'MenuField tests.'

        self._test_one(MenuField)

    def test_checkboxes( self ):
        'CheckboxesField tests.'

        self._test_many(CheckboxesField)

    def test_listbox( self ):
        'ListboxField tests.'

        self._test_one(ListboxField)
        self._test_many(ListboxField, multiple=1)

    def test_jsdate( self ):
        'JSDateField tests.'

        # Test simple.
        f = Form('test-form', JSDateField('birthday'))

        p = FormParser(f)
        try:
            # This will assert because the birthday is always expected and we're
            # supposed to take care of hidden inconsistencies ourselves.
            p.parse({}) 
            assert 0 
        except AssertionError: pass

        p = FormParser(f)
        p.parse({'birthday': '20051003'})
        assert not p.haserrors() and p['birthday'] == datetime.date(2005, 10, 03)

        p = FormParser(f)
        try:
            # This will assert because the value is just plain wrong and it is
            # not a user error.
            p.parse({'birthday': 'Thu, Jan 01, 2005'})
            assert 0 
        except AssertionError: pass

#-------------------------------------------------------------------------------
#
class TestRender:
    """
    Tests for rendering.
    """

    def test_hidden( self ):
        'Test rendering hidden fields.'

        # Expect an error on trying to render a hidden field without a value.
        f = Form('test-form', StringField('name', hidden=1))
        args = {}
        p = FormRenderer(f, incomplete=1)
        try:
            p.render()
            assert False
        except RuntimeError:
            pass

    def test_incomplete( self ):
        'Test rendering incompletely.'

        # Expect an error on trying to render a hidden field without a value.
        f = Form('test-form', StringField('name'))
        args = {}
##         p = FormRenderer(f, incomplete=1)
##         p.render('name')
# Bring this back when we will have the simple renderer class.
        
        # Note: we cannot really test the destructor failure, because the
        # exception is ignored from there, due to its presence in the __del__()
        # call, and all it does is output a message to stderr.

    def test_nonexistent( self ):
        'Test rendering fields that do not exist.'

        # Expect an error on trying to render a hidden field without a value.
        f = Form('test-form', StringField('name', hidden=1))
        args = {}
        p = FormRenderer(f, incomplete=1)
        try:
            p.render(only='notexist')
            assert False
        except RuntimeError:
            pass

    #---------------------------------------------------------------------------

    harness = """
<html>
  <meta>
    <style type="text/css"/><!--

.form-error { color: red; font-size: smaller; }

.form-table { 
  margin-left: auto;
  margin-right: auto;
}

td.form-label {
  padding-left: 1em;
  padding-right: 1em;
  background-color: #F4F4F8;
}

div#the-form {
  text-align: center;
  width: 800px;
  margin-left: auto;
  margin-right: auto;
  background-color: #FAFDFA;
}

--></style>
  </meta>
<body>
<div id="the-form">
%s
</div>
</body>
</html>
"""
    
    tmpfilename = '/tmp/test.html'
    
    def print_render( self, text ):
        """
        Renderer supporting the inspection of test HTML output.
        """
        f = StringIO.StringIO()
        print >> f, self.harness % text
        html = f.getvalue()

        # Print output to stdout.
        print
        print html
        print
        
        # Also print output to a file that a browser can point at.
        file(self.tmpfilename, 'w').write(html)

        # Open it automatically in the web browser.
        webbrowser.open(self.tmpfilename)

    def test_visual( self ):
        'Visual tests examining the output of the renderer.'
        
        f = create_demo_form()
        values = {'name': u'Martin Blais',
                  'number': 17,
                  'description': u"A really nice guy. Guapo."}
        errors = {'name': u'Idiotic error'}
        p = TextFormRenderer(f, values, errors, incomplete=1)
        self.print_render(p.render())

#-------------------------------------------------------------------------------
#
def create_demo_form():
    """
    Create a form for demo/test.
    """
    f = Form('test-form',
         StringField('name', N_("Person's name")),
         TextAreaField('description', N_("Description"), rows=10, cols=60),
         DateField('birthday', N_("Birthday")),
         EmailField('email', N_("Email")),
         URLField('homepage', N_("Home Page")),
         IntField('number', N_("Age")),
         IntField('height', N_("Height")),
         BoolField('confirm', N_("Are you sure?")),
         action='handler')

    return f
