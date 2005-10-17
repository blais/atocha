#!/usr/bin/env python
#
# $Id$
#

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


# stdlib imports.
import cgi


__all__ = ['ArgsNormalizer']


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

