import wsynphot
import os
from astropy.io import fits
from astropy import units as u
from spectrum1d import SKSpectrum1D as Spectrum1D

default_vega = 'alpha_lyr_mod_001.fits'

def get_calibration_dir(fname):
    return os.path.join(wsynphot.__path__[0], 'data', 'calibration', fname)

def get_vega(vega_file=None):
    if vega_file is None:
        vega_file = default_vega
    vega_table = fits.getdata(get_calibration_dir(vega_file), extension=1)
    vega = Spectrum1D.from_array(vega_table['wavelength'] * u.angstrom,
                                 vega_table['flux'] *
                                 u.erg / u.s/ u.cm**2 / u.angstrom)

    return vega