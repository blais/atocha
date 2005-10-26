#!/usr/bin/env python
#
# $Id$
#

"""
Normalizer for Apache + mod_python + Draco.
"""

# atocha imports.
from atocha.norm import ArgsNormalizer


__all__ = ['DracoNormalizer']


#-------------------------------------------------------------------------------
#
class DracoNormalizer(ArgsNormalizer):
    """
    Noop normalizer for Draco, which already normalizes from mod_python.
    """
    def normalize( self, args ):
        # Convert from DracoNamespace to a Python dict.
        return dict(args)

