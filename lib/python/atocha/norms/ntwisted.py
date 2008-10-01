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
Normalizer for Twisted.Web arguments.
"""

# atocha imports
from atocha.fields.uploads import FileUpload


__all__ = ('normalize',)



def normalize_args(parser, form):
    """
    Normalizer for Python's cgi library.
    """
    args = {}
    for varname in form.keys():
        value = form[varname]

## FIXME: we need to figure out what Twisted provides for us for file uploads.
        if (False
            #isinstance(value, cgi.FieldStorage) and 
            #isinstance(value.file, file)
            ):

            ovalue = FileUpload(value, value.filename)

        else:
            if len(value) == 1:
                ovalue = value[0]
            else:
                ovalue = value

        args[varname] = ovalue

    return args




