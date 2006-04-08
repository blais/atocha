#!/usr/bin/env python
#
# $Id$
#
#  Atocha -- A web forms rendering and handling Python library.
#  Copyright (C) 2005  Martin Blais
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
Time and Date Fields
"""

# stdlib imports
import re, datetime, locale
from types import NoneType

# atocha imports.
from atocha import AtochaInternalError
from atocha.field import Field, FieldError, OptRequired
from atocha.messages import msg_registry
from texts import StringField
from choices import MenuField


__all__ = ['DateField', 'JSDateField', 'DateMenuField']


#-------------------------------------------------------------------------------
#
class DateField(StringField):
    """
    A string field that accepts strings that represent dates, in some specific
    formats.
    """
    types_data = (NoneType, datetime.date,)
    types_parse = (NoneType, unicode,)
    types_render = (unicode,)
    css_class = 'date'

    attributes_delete = ('strip', 'minlen', 'maxlen')


    __def_display_fmt = '%a, %d %B %Y' # or '%x'

    # Support ISO-8601 format.  
    __date_re1 = re.compile('(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)')

    # Support a natural format, like 11 Sep 2001, or Sep 11, 2001
    __date_re2 = re.compile('(?P<day>\d+)\s+(?P<nmonth>\w+)\s+(?P<year>\d+)')
    __date_re3 = re.compile('(?P<nmonth>\w+)\s+(?P<day>\d+)[\s,]+(?P<year>\d+)')

    # Pre-fetch lists of constants for month locale lookups.
    _mon_list = [getattr(locale, 'MON_%d' % x) for x in xrange(1, 13)]
    _abmon_list = [getattr(locale, 'ABMON_%d' % x) for x in xrange(1, 13)]

    def __init__( self, name, label=None, **attribs ):
        DateField.validate_attributes(attribs)

        attribs.setdefault('size', 20)
        attribs['strip'] = True
        StringField.__init__(self, name, label, **attribs)

    def parse_value( self, pvalue ):
        value = StringField.parse_value(self, pvalue)
        assert isinstance(value, unicode)
        
        # Indicate that this field has not been sent.
        if not value:
            return None

        # Check formats.
        for fre in self.__date_re1, self.__date_re2, self.__date_re3:
            mo = fre.match(value)
            if mo:
                break
        else:
            raise FieldError(msg_registry['date-invalid-format'] % value, value)

        year, day = map(int, mo.group('year', 'day'))
        try:
            month = int(mo.group('month'))
        except IndexError, e:
            # Get abbreviated and full month names.
            enc = locale.getpreferredencoding()
            abmons = [locale.nl_langinfo(x).decode(enc)
                      for x in self._abmon_list]
            mons = [locale.nl_langinfo(x).decode(enc)
                    for x in self._mon_list]

            nmonth = mo.group('nmonth')

            try:
                month = abmons.index(nmonth.capitalize()) + 1
            except ValueError, e:
                try:
                    month = mons.index(nmonth.capitalize()) + 1
                except ValueError, e:
                    raise FieldError(
                        msg_registry['date-invalid-month'] % nmonth, value)

        assert type(month) is int
            
        # Convert into date.
        try:
            dvalue = datetime.date(year, month, day)
        except ValueError, e:
            raise FieldError(msg_registry['date-invalid'] % value,
                             value)

        return dvalue

    def render_value( self, dvalue ):
        if dvalue is None:
            return u''

        # Convert the date object in a format suitable for rendering it.
        rvalue = dvalue.isoformat().decode('ascii')
        return rvalue

    def display_value( self, dvalue ):
        if dvalue is None:
            return u''
        return time_to_string(dvalue, self.__def_display_fmt)


#-------------------------------------------------------------------------------
#
class JSDateField(Field, OptRequired):
    """
    A fancy Javascript-based date field.

    This is an adaptation for this form handling library of a nice
    Javascript-based date input field found at http://www.jasonmoon.net/.  The
    conditions of utilisation of that code is that a notice should be present
    and kept intact somewhere in the comments.
    """
    types_data = (datetime.date, NoneType)
    types_parse = (NoneType, unicode,)
    types_render = (unicode,)
    css_class = 'jsdate'

    # Public data used for adding the script reference to the head.
    scripts = (('calendarDateInput.js',
               u"""Jason's Date Input Calendar- By Jason Moon
               http://www.jasonmoon.net/ Script featured on and available at
               http://www.dynamicdrive.com Keep this notice intact for use.
               """),)

    __date_re = re.compile('(\d\d\d\d)(\d\d)(\d\d)')

    __script_re = '^[a-zA-Z_]+$'

    def __init__( self, name, label=None, **attribs ):
        JSDateField.validate_attributes(attribs)

        # Note: there is a special constraint on the varname of the field due to
        # the Javascript code involved (see below).  This verification is
        # required for the JS calendar.
        assert re.match(JSDateField.__script_re, name)

        OptRequired.__init__(self, attribs, True)
        Field.__init__(self, name, label, attribs)
        
        self.required = bool(attribs.pop('required', False))
        assert isinstance(self.required, bool)


    def parse_value( self, pvalue ):
        # Check if no value submitted... this would be strange, since this field
        # should always send us a value (except when not required explicitly),
        # even without user edits.
        pvalue = OptRequired.parse_value(self, pvalue)

        if pvalue:
            # Encode value into ascii.
            try:
                dvalue = pvalue.encode('ascii')
            except UnicodeEncodeError:
                # This should not happen if the value comes from the code.
                raise AtochaInternalError(
                    "Error: internal error with input from JSDateField.")

            # Match the given string, it should always match.
            mo = JSDateField.__date_re.match(dvalue)
            if mo is None:
                raise AtochaInternalError(
                    "Error: internal error with input from JSDateField.")

            # Convert into date.
            try:
                dvalue = datetime.date(*map(int, mo.groups()))
            except ValueError, e:
                raise FieldError(msg_registry['date-invalid'] % pvalue)
        else:
            assert not self.required
            dvalue = None

        return dvalue

    def render_value( self, dvalue ):
        if dvalue is None:
            return u''

        # Convert the date object in a format suitable for being accepted by the
        # Javascript code. Note: this may not work before 1900.
        rvalue = dvalue.strftime('%Y%m%d')
        return rvalue.decode('ascii')

    def display_value( self, dvalue ):
        assert dvalue is not None
        return time_to_string(dvalue, DateField.__def_display_fmt)


#-------------------------------------------------------------------------------
#
class DateMenuField(MenuField):
    """
    A field that offers dates in close proximity, via a select menu.
    """
    types_data = (datetime.date, NoneType,)
    css_class = 'datemenu'

    attributes_delete = ('choices', 'nocheck')

    attributes_declare = (
        ('any', 'str',
         """Set this to some string if the field should support entering a value
         for any/unspecified date.  The string will be displayed in the dates
         menu and a value of None will be returned by the widget if it is
         selected."""),

        ('nbdays', 'int',
         """The number of days to display from today."""),
        )

    __def_nbdays = 30

    __value_fmt = '%Y-%m-%d'
    __def_display_fmt = '%a, %d %B %Y' # or '%x'

    # Support ISO-8601 format.  
    __date_re1 = re.compile('(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)')

    def __init__( self, name, label=None, **attribs ):
        DateMenuField.validate_attributes(attribs)

        self.nbdays = int(attribs.pop('nbdays', self.__def_nbdays))
        assert isinstance(self.nbdays, int)
        assert self.nbdays > 0

        self.any = attribs.pop('any', None)
        if self.any:
            assert isinstance(self.any, str)

        attribs['nocheck'] = True
        MenuField.__init__(self, name, [], label, **attribs)

        # Note: The set of dates will be filled in every time we render this
        # field, rather than at initialization time, to avoid long-running
        # children eventually having invalid dates, so we do not initialize the
        # menu's choices in the constructor.

    def parse_value( self, pvalue ):
        value = MenuField.parse_value(self, pvalue)

        # Indicate that this field has not been sent.
        if not value:
            return None

        # Support the 'any' value.
        if value == 'any':
            assert self.any
            return None

        # Convert from value string to a datetime.date object.
        mo = self.__date_re1.match(value)
        if not mo:
            raise FieldError(msg_registry['date-invalid'] % value, value)
        try:
            dvalue = datetime.date(*map(int, mo.groups()))
        except ValueError, e:
            raise FieldError(msg_registry['date-invalid'] % value, value)

        return dvalue

    def render_value( self, dvalue ):
        self._reset_dates()

        # Convert date to its corresponding value string.
        rvalue = None
        if dvalue is not None:
            rvalue = dvalue.strftime(self.__value_fmt)
        else:
            if self.any:
                rvalue = 'any'
            else:
                raise AtochaInternalError(
                    "Error: internal error rendering DateMenuField.")

        return rvalue

    def display_value( self, dvalue ):
        if dvalue is None:
            return u''
        return time_to_string(dvalue, self.__def_display_fmt)

    def _reset_dates( self ):
        """
        Reset the list of dates (choices) for this menu.
        """
        choices = []
        if self.any:
            choices.append( ('any', self.any) )
            
        # Set the list of dates to this choice field.
        for d in date_range(self.nbdays):
            choices.append( (d.strftime(self.__value_fmt),
                             time_to_string(d, self.__def_display_fmt)) )
        self.setchoices(choices)


#-------------------------------------------------------------------------------
#
def time_to_string( date, fmt ):
    """
    Convert a date object to a unicode string.  We need this because
    strftime has calendar limitations on years before 1900.
    """
    if date.year < 1900:
        # Use simplistic format for old dates.
        return u'%d-%d-%d' % (date.year, date.month, date.day)
    else:
        # Note: what encoding does the time module return the format in?
        # i.e. We never use the default encoding in this library.
        return date.strftime(fmt)


#-------------------------------------------------------------------------------
#
def date_range( nbsteps, basedate=None, step=None ):
    """
    Yield a range of dates, for 'nbsteps' steps, starting from 'basedate' or
    today's date, if not set, and stepping by 'step', or one-day increments, if
    not set.
    """
    # Set defaults.
    if basedate is None:
        basedate = datetime.date.today()
    if step is None:
        step = datetime.timedelta(days=1)

    for s in xrange(nbsteps):
        yield basedate
        basedate += step

