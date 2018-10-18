# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This is an Astropy affiliated package.
"""
import os
on_rtd = os.environ.get('READTHEDOCS') == 'True'
# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *

if not on_rtd:
    # ----------------------------------------------------------------------------

    # For egg_info test builds to pass, put package imports here.
    print "I'm not on ReadTheDocs and importing nothing"
    if not _ASTROPY_SETUP_:
        from wsynphot.base import BaseFilterCurve, FilterCurve, FilterSet, MagnitudeSet
        from wsynphot.calibration import get_vega
        from wsynphot.spectrum1d import SKSpectrum1D as Spectrum1D
else:
    print "I'm on ReadTheDocs and importing nothing"