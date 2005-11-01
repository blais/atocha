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


# Explicit inheritance search snippet.

            # Search the classes in order of inheritance.
            clsstack = [field.__class__]
            method = None
            while method is None:
                cls = clsstack.pop()
                mname = 'render%s' % cls.__name__
                method = getattr(renderer, mname, None)
                clsstack.extend(cls.__bases__)

            if method is None:
                raise AtochaInternalError(
                    "Error: renderer has no method for '%s'." %
                    field.__class__)
