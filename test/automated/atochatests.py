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
import unittest 
from pprint import pprint, pformat


# form imports.
from atocha import *


# Disable implicit unicode conversions, at least for these automated tests.
# In this library we try not to use the default encoding anywhere but explicitly.
reload(sys); sys.setdefaultencoding('undefined')


#-------------------------------------------------------------------------------
#
class Test(unittest.TestCase):
    """
    Base class for tests. We just use this for its assert functions.
    """
    def __init__( self ):
        pass

#-------------------------------------------------------------------------------
#
class TestSimple(Test):
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
        o = p.end()

        # Test accessor methods.
        name = p['name'] # Using accessor.
        name = o.name # Using accessor.
        self.assertRaises(KeyError, getattr, o, 'name2')
        self.assertEqual(o.name, u'école')


#-------------------------------------------------------------------------------
#
class TestForm(Test):
    """
    Test form functionalities.
    """

    # FIXME: we need to check the basic form functionalities here.


#-------------------------------------------------------------------------------
#
class TestRender(Test):
    """
    Tests for rendering.
    """

    def test_validity( self ):
        "Test the completeness of a renderer's implementation."
        f = Form('test-form')
        TextFormRenderer.validate_renderer()
        # Note: test the htmlout renderer here too.

    def test_hidden( self ):
        'Test rendering hidden fields.'

        # Expect an error on trying to render a hidden field without a value.
        f = Form('test-form', StringField('name', state=Field.HIDDEN))
        args = {}
        p = TextFormRenderer(f, incomplete=1)
        self.assertRaises(AtochaError, p.render)

    def test_incomplete( self ):
        'Test rendering incompletely.'

        # Expect an error on trying to render a hidden field without a value.
        f = Form('test-form', StringField('name'))
        args = {}
        p = TextFormRenderer(f, incomplete=1)
        p.render(only=['name'], action='bli')
        
        # Note: we cannot really test the destructor failure, because the
        # exception is ignored from there, due to its presence in the __del__()
        # call, and all it does is output a message to stderr.

    def test_nonexistent( self ):
        'Test rendering fields that do not exist.'

        # Expect an error on trying to render a hidden field without a value.
        f = Form('test-form', StringField('name', state=Field.HIDDEN))
        args = {}
        p = FormRenderer(f, incomplete=1)
        self.assertRaises(AtochaError, p.render, only=['notexist'])

    def test_encoding( self ):
        'Test output encoding for text renderer.'

        f = Form('test-form',
                 StringField('name', state=Field.HIDDEN),
                 action='handle.cgi')
        args = {'name': u'Mélanie'}
        r = TextFormRenderer(f, args)
        assert isinstance(r.render(), unicode)

        r = TextFormRenderer(f, args, output_encoding='latin-1')
        assert isinstance(r.render(), str)


    #---------------------------------------------------------------------------

    harness = u"""
<html>
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
        f.write(self.harness % text)
        html = f.getvalue()

        if 0:
            # Print output to stdout.
            print
            print html
            print
        
        if 0:
            # Also print output to a file that a browser can point at.
            file(self.tmpfilename, 'w').write(html.encode('utf-8'))

            # Open it automatically in the web browser.
            webbrowser.open(self.tmpfilename)

    def test_visual( self ):
        'Visual tests examining the output of the renderer.'
        
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

        values = {'name': u'Martin Blais',
                  'number': 17,
                  'description': u"A really nice guy. Guapo."}
        errors = {'name': u'Idiotic error'}

        p = TextFormRenderer(f, values, errors, incomplete=1)
        self.print_render(p.render())



#-------------------------------------------------------------------------------
#
_u8str = u'école'.encode('utf-8')

class TestFields(Test):
    """
    Tests for specific fields.
    """

    def test_string( self ):
        'StringField tests.'

        # Test without a label.
        f = Form('test-form', StringField('name'))
        args = {'name': _u8str}
        p = FormParser(f, args, end=1)
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
        p = FormParser(f, args=args, end=1)
        assert p['nameuni'] == u'\xe9cole' and type(p['nameuni']) is unicode
        assert p['nameutf'] == '\xc3\xa9cole' and type(p['nameutf']) is str
        assert p['namelatin'] == '\xe9cole' and type(p['namelatin']) is str
        assert p['nameascii'] == 'ecole' and type(p['nameascii']) is str
        assert not p.haserrors()

        # Test string encoding errors.
        args = {'nameascii': _u8str}
        p = FormParser(f, args, end=1)
        assert p['nameascii'] is None
        assert p.haserrors()
        assert p.geterrors().keys() == ['nameascii']

        # Test required field.
        f = Form('test-form', StringField('name', required=1))
        args = {}
        p = FormParser(f, args, end=1)
        assert p.haserrors()
        assert p.geterrors().keys() == ['name']
        assert p['name'] is None

        # Test with multiline input.
        f = Form('test-form', StringField('name', minlen=4, maxlen=10))
        args = {'name': 'Martin\nblibli\nlis'}
        p = FormParser(f, args, end=1)
        assert p.haserrors()

        # Test min/max lengths.
        f = Form('test-form', StringField('name', minlen=4, maxlen=10))
        args = {'name': 'Martin'}
        p = FormParser(f, args, end=1)
        assert not p.haserrors()

        args = {'name': 'Jon'}
        p = FormParser(f, args, end=1)
        assert p.haserrors()

        args = {'name': 'Elizabeth the 3rd'}
        p = FormParser(f, args, end=1)
        assert p.haserrors()

        # Test strip option.
        f = Form('test-form', StringField('name', strip=1))
        args = {'name': ' Martin  '}
        p = FormParser(f, args, end=1)
        assert not p.haserrors()
        assert p['name'] == u'Martin'

    def test_textarea( self ):
        'Textarea tests.'
        
        # Test strip option.
        f = Form('test-form', TextAreaField('quote', N_('Quote')))

        args1 = {'quote': u"""When I hear people complain about Lisp's parentheses,
        it sounds to my ears like someone saying: 'I tried one of those bananas,
        which you say are so delicious. The white part was ok, but the yellow
        part was very tough and tasted awful.'""".encode(f.accept_charset)}

        args2 = {'quote': u"""Aller a l'école,
        c'est pas juste pour les bollés.""".encode(f.accept_charset)}

        p = FormParser(f, args1, end=1)
        assert not p.haserrors()
        assert p['quote']
        
        p = FormParser(f, args2, end=1)
        assert not p.haserrors()
        assert p['quote']


    def test_date( self ):
        'DateField tests.'

        # Test simple.
        f = Form('test-form', DateField('birthday'))

        p = FormParser(f, {}, end=1)
        assert not p.haserrors() and p['birthday'] is None
        
        f = Form('test-form', DateField('birthday', required=1))

        p = FormParser(f, {}, end=1)
        assert p.haserrors() and 'birthday' in p.geterrors()

        for x in '1972-05-28', '28 may 1972', 'May 28, 1972', 'May 28 1972':
            p = FormParser(f, {'birthday': x}, end=1)
            assert not p.haserrors()
            assert p['birthday'] == datetime.date(1972, 05, 28)

        p = FormParser(f, {'birthday': 'Thu, Jan 01, 2005'}, end=1)
        assert p.haserrors() and 'birthday' in p.geterrors()


    def test_email( self ):
        'EmailField tests.'

        f = Form('test-form', EmailField('email'))

        p = FormParser(f, {'email': 'blais@furius.ca'}, end=1)
        assert not p.haserrors() and p['email'] == 'blais@furius.ca'

        p = FormParser(f, {'email': 'Martin Blais <blais@furius.ca>'}, end=1)
        assert not p.haserrors() and p['email'] == 'blais@furius.ca'
        
        p = FormParser(f, {'email': 'blais'}, end=1)
        assert p.haserrors() and p.geterrorfields() == ['email']

        f2 = Form('test-form', EmailField('email', accept_local=1))
        p = FormParser(f2, {'email': 'blais'}, end=1)
        assert not p.haserrors() and p['email'] == 'blais'

        p = FormParser(f, {'email': 'blais+bli@furius.ca'}, end=1)
        assert not p.haserrors() and p['email'] == 'blais+bli@furius.ca'

        p = FormParser(f, {'email': 'blais@furius.org'}, end=1)
        assert not p.haserrors() and p['email'] == 'blais@furius.org'

        p = FormParser(f, {'email': 'blais[@furius.com'}, end=1)
        assert p.haserrors() and p['email'] is None

        # TLDs are not checked, it seems. We'll take it.
        # p = FormParser(f, {'email': 'blais@furius.glu'}, end=1)
        # assert p.haserrors() and p.geterrorfields() == ['email']

    def test_url( self ):
        'URLField tests.'

        ## FIXME: todo

    def test_int( self ):
        'IntField tests.'

        # Test simple.
        f = Form('test-form', IntField('number', minval=3, maxval=20))

        p = FormParser(f, {'number': '17'}, end=1)
        assert not p.haserrors()
        assert p['number'] == 17

        p = FormParser(f, {'number': '2'}, end=1)
        assert p.haserrors() and 'number' in p.geterrors()

        p = FormParser(f, {'number': '25'}, end=1)
        assert p.haserrors() and 'number' in p.geterrors()

        p = FormParser(f, {'number': '17.3'}, end=1)
        assert p.haserrors() and 'number' in p.geterrors()

        # Test required.
        f = Form('test-form', IntField('number', required=1))
        p = FormParser(f, {}, end=1)
        assert p.haserrors() and 'number' in p.geterrors()

    def test_float( self ):
        'FloatField tests.'

        # Test simple.
        f = Form('test-form', FloatField('number', minval=3.2, maxval=20.7))

        p = FormParser(f, {'number': '17.3'}, end=1)
        assert not p.haserrors()
        assert p['number'] == 17.3

        p = FormParser(f, {'number': '17'}, end=1)
        assert not p.haserrors()
        assert p['number'] == 17

        p = FormParser(f, {'number': '2.03'}, end=1)
        assert p.haserrors() and 'number' in p.geterrors()

        p = FormParser(f, {'number': '25.87'}, end=1)
        assert p.haserrors() and 'number' in p.geterrors()

        # Test required.
        f = Form('test-form', IntField('number', required=1))
        p = FormParser(f, {}, end=1)
        assert p.haserrors() and 'number' in p.geterrors()

    def test_bool( self ):
        'BoolField tests.'

        # Test simple.
        f = Form('test-form', BoolField('agree'))

        p = FormParser(f, {}, end=1)
        assert not p.haserrors() and p['agree'] is False
        
        p = FormParser(f, {'agree': 'bullshyte'}, end=1)
        assert not p.haserrors() and p['agree'] is True

        p = FormParser(f, {'agree': ''}, end=1)
        assert not p.haserrors() and p['agree'] is False

    def _test_one( self, cls, **extra ):
        'One choices test.'

        # Simple tests.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'), **extra))
        
        p = FormParser(f, {'coffee': 'latte'}, end=1)
        assert not p.haserrors() and p['coffee'] == 'latte'

        p = FormParser(f)
        self.assertRaises(AtochaError, p.parse, {'coffee': ['latte', 'expresso']})
        p.end()

        p = FormParser(f)
        self.assertRaises(AtochaError, p.parse, {'coffee': 'american'})
        p.end()

        # Test with labels.
        f = Form('test-form',
                 cls('coffee', [('latte', N_('Latte')),
                                ('expresso', N_('Expresso')),
                                ('moccha', N_('Moccha'))], **extra))

        p = FormParser(f, {'coffee': 'expresso'}, end=1)
        assert not p.haserrors() and p['coffee'] == 'expresso'


        # Test with integer values.
        f = Form('test-form',
                 cls('coffee', [(10, N_('Latte')),
                                (20, N_('Expresso')),
                                (30, N_('Moccha'))], **extra))

        p = FormParser(f, {'coffee': '10'}, end=1)
        assert not p.haserrors() and p['coffee'] == '10'


        # Test with disabled value check.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'),
                     nocheck=1, **extra))

        p = FormParser(f, {'coffee': 'american'}, end=1)
        assert not p.haserrors() and p['coffee'] == 'american'


    def _test_many( self, cls, **extra ):
        'Many choices tests.'

        # Simple tests.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'), **extra))

        p = FormParser(f, {}, end=1)
        assert not p.haserrors() and p['coffee'] == []
        
        p = FormParser(f, {'coffee': 'latte'}, end=1)
        assert not p.haserrors() and p['coffee'] == ['latte']

        p = FormParser(f, {'coffee': ['latte', 'expresso']}, end=1)
        assert not p.haserrors() and p['coffee'] == ['latte', 'expresso']

        p = FormParser(f)
        self.assertRaises(AtochaError, p.parse, {'coffee': 'american'})
        p.end()

        # Test with labels.
        f = Form('test-form',
                 cls('coffee', [('latte', N_('Latte')),
                                ('expresso', N_('Expresso')),
                                ('moccha', N_('Moccha'))], **extra))

        p = FormParser(f, {'coffee': 'expresso'}, end=1)
        assert not p.haserrors() and p['coffee'] == ['expresso']


        # Test with integer values.
        f = Form('test-form',
                 cls('coffee', [(10, N_('Latte')),
                                (20, N_('Expresso')),
                                (30, N_('Moccha'))], **extra))

        p = FormParser(f, {'coffee': '10'}, end=1)
        assert not p.haserrors() and p['coffee'] == ['10']


        # Test with disabled value check.
        f = Form('test-form',
                 cls('coffee', ('latte', 'expresso', 'moccha'),
                     nocheck=1, **extra))

        p = FormParser(f, {'coffee': 'american'}, end=1)
        assert not p.haserrors() and p['coffee'] == ['american']


    def test_radio( self ):
        'RadioField tests.'

        self._test_one(RadioField)

    def test_menu( self ):
        'MenuField tests.'

        self._test_one(MenuField)

        # Test errors on zero submitted args.
        f = Form('test-form',
                 MenuField('coffee', ('latte', 'expresso', 'moccha')))
        p = FormParser(f, {}, end=1)
        assert p.haserrors() and 'coffee' in p.geterrors()

    def test_checkboxes( self ):
        'CheckboxesField tests.'

        self._test_many(CheckboxesField)

    def test_listbox( self ):
        'ListboxField tests.'

        self._test_one(ListboxField)

        # Test zero selected values.
        f = Form('test-form',
                 ListboxField('coffee', ('latte', 'expresso', 'moccha')))
        p = FormParser(f, {}, end=1)
        assert not p.haserrors() and p['coffee'] is None           

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
        p.end()
        
        p = FormParser(f, {'birthday': '20051003'}, end=1)
        assert not p.haserrors() and p['birthday'] == datetime.date(2005, 10, 03)

        p = FormParser(f)
        # This will assert because the value is just plain wrong and it is
        # not a user error.
        self.assertRaises(AtochaError, p.parse, {'birthday': 'Thu, Jan 01, 2005'})
        p.end()

    def test_fileupload( self ):
        'FileUpload tests.'
        
        contents = 'FILE CONTENTS'
        class Obj: pass
        def crfile():
            o = Obj()
            o.file = StringIO.StringIO(contents)
            return FileUpload(o)

        f = Form('test-form', FileUploadField('myfile', 'My File'))

        p = FormParser(f, {}, end=1)
        assert p['myfile'] is None

        p = FormParser(f, {'myfile': crfile()}, end=1)
        assert isinstance(p['myfile'], FileUpload)
        assert p['myfile'].read() == contents

        #
        # Test the SetFile field.
        #

        f = Form('test-form', SetFileField('setfile', 'Set File'))

        p = FormParser(f, {}, end=1)
        assert p['setfile'] is None

        p = FormParser(f, {'setfile': crfile()}, end=1)
        assert isinstance(p['setfile'], FileUpload)
        assert p['setfile'].read() == contents

        p = FormParser(f, {'setfile_reset': '1'}, end=1)
        assert p['setfile'] is False

        p = FormParser(f, {'setfile': crfile(), 'setfile_reset': '1'}, end=1)
        assert p['setfile'] is False

