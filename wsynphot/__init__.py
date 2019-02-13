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
    if not _ASTROPY_SETUP_:
        from wsynphot.base import (BaseFilterCurve, FilterCurve, FilterSet,
                                   MagnitudeSet, list_filters)
        from wsynphot.calibration import get_vega
        from wsynphot.spectrum1d import SKSpectrum1D as Spectrum1D
        from wsynphot.data.base import (
            delete_filter_data, download_filter_data,
            ALPHA_LYR_PATH, ALPHA_LYR_FNAME)
