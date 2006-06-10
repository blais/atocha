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
Normalizer for Apache + mod_python.
"""

# mod_python imports
from mod_python.util import FieldStorage, Field

# atocha imports
from atocha.fields.uploads import FileUpload


__all__ = ('normalize',)


#-------------------------------------------------------------------------------
#
def normalize_args( parser, mpreq ):
    """
    Normalizer for Python's cgi library.
    """
    args = {}
    fs = FieldStorage(mpreq)

    # Cast down from the FieldStorage object to Python str.
    for name in fs.keys():
        value = fs[name]
        if isinstance(value, str):
            value = str(value)

        elif isinstance(value, Field):
            value = FileUpload(value)

        elif isinstance(value, list):
            for i in range(len(value)):
                if isinstance(value[i], str):
                    value[i] = str(value[i])

                elif isinstance(value[i], Field):
                    value[i] = FileUpload(value[i])

        if name:  # mod_python sometimes gives a None key
            args[name] = value

    return args

