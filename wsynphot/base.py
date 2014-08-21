# defining the base filter curve classes

from scipy import interpolate
from specutils import Spectrum1D


class BaseFilterCurve(object):
    """
    Basic filter curve class

    Parameters
    ----------

    wavelength: ~astropy.units.Quantity
        wavelength for filter curve

    transmission: numpy.ndarray
        transmission for filter curve

    interpolation_kind: str
        allowed interpolation kinds given in scipy.interpolate.interp1d
    """

    def __init__(self, wavelength, transmission, interpolation_kind='linear'):
        if not hasattr(wavelength, 'unit'):
            raise ValueError('the wavelength needs to be a astropy quantity')
        self.wavelength = wavelength
        self.transmission = transmission

        self.interpolation_object = interpolate.interp1d(self.wavelength,
                                                         self.transmission,
                                                         kind=interpolation_kind,
                                                         bounds_error=False,
                                                         fill_value=0.0)


    def __mul__(self, other):
        if not hasattr(other, 'flux') or not hasattr(other, 'wavelength'):
            raise ValueError('requiring a specutils.Spectrum1D-like object that'
                             'has attributes "flux" and "wavelength"')
        transmission = self.interpolate(other.wavelength)

        return Spectrum1D(transmission * other.flux, wcs=other.wcs)


    def interpolate(self, wavelength):
        """
        Interpolate the filter onto new wavelength grid

        Parameters
        ----------

        wavelength: ~astropy.units.Quantity
            wavelength grid to interpolate on

        """

        converted_wavelength = wavelength.to(self.wavelength.unit)
        return self.interpolation_object(converted_wavelength)

class FilterCurve(BaseFilterCurve):
    pass