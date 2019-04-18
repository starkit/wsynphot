import wsynphot
import os
from astropy.io import fits
from astropy import units as u
from wsynphot.spectrum1d import SKSpectrum1D as Spectrum1D
from wsynphot.data.base import ALPHA_LYR_FNAME, ALPHA_LYR_PATH

default_vega_path = ALPHA_LYR_PATH

def get_calibration_dir(fname):
    return os.path.join(wsynphot.__path__[0], 'data', 'calibration', fname)

def get_vega(vega_file=None):
    if vega_file is None:
        vega_file = default_vega_path
    if not os.path.exists(vega_file):
        raise IOError('Calibration file {0} does not exist - please download by'
                      'using wsynphot.download_calibration() or '
                      'wsynphot.download_all()'.format(vega_file))
    vega_table = fits.getdata(vega_file, extension=1)
    vega = Spectrum1D.from_array(vega_table['wavelength'] * u.angstrom,
                                 vega_table['flux'] *
                                 u.erg / u.s/ u.cm**2 / u.angstrom)

    return vega
