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
Normalizer for Apache + mod_python + Draco.
"""

# atocha imports
from atocha.norm import ArgsNormalizer
from atocha.fields.uploads import FileUpload

# draco imports
from draco.request import FileUpload as DracoUpload


__all__ = ['DracoNormalizer']


#-------------------------------------------------------------------------------
#
class DracoNormalizer(ArgsNormalizer):
    """
    Noop normalizer for Draco, which already normalizes from mod_python.
    """
    def normalize( self, args ):
        # Convert from DracoNamespace to a Python dict.

        newargs = {}
        for k, v in args.iteritems():
            if isinstance(v, DracoUpload):
                newargs[k] = FileUpload(v.field)
            else:
                newargs[k] = v

        return newargs

