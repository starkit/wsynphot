# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This is an Astropy affiliated package.
"""
import sys, os
# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *

from wsynphot.util.colored_logger import ColoredFormatter, formatter_message
import logging


# For egg_info test builds to pass, put package imports here.
if not _ASTROPY_SETUP_:
    from wsynphot.base import (BaseFilterCurve, FilterCurve, FilterSet,
                               MagnitudeSet, list_filters)
    from wsynphot.calibration import get_vega_calibration_spectrum
    from wsynphot.spectrum1d import SKSpectrum1D as Spectrum1D
    from wsynphot.data.base import (download_calibration_data, 
        ALPHA_LYR_PATH, ALPHA_LYR_FNAME)

FORMAT = "[%(levelname)-18s] [$BOLD%(name)-20s$RESET] %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
COLOR_FORMAT = formatter_message(FORMAT, True)

logging.captureWarnings(True)
logger = logging.getLogger('wsynphot')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_formatter = ColoredFormatter(COLOR_FORMAT)
console_handler.setFormatter(console_formatter)

logger.addHandler(console_handler)
logging.getLogger('py.warnings').addHandler(console_handler)