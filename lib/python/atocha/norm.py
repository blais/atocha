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
Argument normalization interface.

Interface for calling the argument normalizers, which act as a layer to adapt
from the incoming web framework arguments to a dict with expected data types.

Note that we do not include all the possible normalizers on purpose, because the
normalizers will necessarily have dependencies that will not be present on all
systems.  The normalizers should be imported individually and typically only
once during the interpreter environment setup to setup the FormParser class with
an appropriate normalizer instance.
"""


__all__ = ('ArgsNormalizer',)


#-------------------------------------------------------------------------------
#
class ArgsNormalizer:
    """
    Base interface for normalizers.
    """
    def normalize( self, submitted_args ):
        """
        Normalize the submitted arguments and return a dict with the normalized
        arguments for parsing.
        """
        raise NotImplementedError

