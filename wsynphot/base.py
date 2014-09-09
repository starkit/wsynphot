# defining the base filter curve classes

from scipy import interpolate
from specutils import Spectrum1D
import wsynphot
import os
filter_data_fname = os.path.join(wsynphot.__path__[0], 'data', 'filter_data.h5')
from pandas import HDFStore
from astropy import units as u, constants as const
import numpy as np
from calibration import get_vega

def calculate_filter_f_lambda(spectrum, filter):
    """
    Calculate the average flux through the filter by evaluating the integral

    ..math::

        f_lambda = \\frac{\\int_}{}
    Parameters
    ----------

    spectrum: ~specutils.Spectrum1D
        spectrum object
    filter: ~wsynphot.FilterCurve

    :return:
    """

    filtered_spectrum = filter * spectrum

    return np.trapz(filtered_spectrum.flux, filtered_spectrum.wavelength)

def calculate_vega_magnitude(spectrum, filter):
    filtered_f_lambda = (calculate_filter_f_lambda(spectrum, filter) /
                         filter.calculate_integral_wavelength())

    return -2.5 * np.log10(filtered_f_lambda / filter.zp_vega_f_lambda)



def calculate_ab_magnitude(spectrum, filter):
    filtered_f_lambda = (calculate_filter_f_lambda(spectrum, filter) /
                         filter.calculate_integral_wavelength())

    return -2.5 * np.log10(filtered_f_lambda / filter.zp_vega_f_lambda)


class BaseFilterCurve(object):
    """
    Basic filter curve class

    Parameters
    ----------

    wavelength: ~astropy.units.Quantity
        wavelength for filter curve

    transmission_lambda: numpy.ndarray
        transmission_lambda for filter curve

    interpolation_kind: str
        allowed interpolation kinds given in scipy.interpolate.interp1d
    """

    @classmethod
    def load_filter(cls, filter_name=None, wavelength_unit=None,
                    interpolation_kind='linear'):
        """

        Parameters
        ----------

        filter_name: str or None

        wavelength_unit: str or astropy.units.Unit
            for some filtersets (e.g. gemini) this can be autodetected

        interpolation_kind: str
            see scipy.interpolation.interp1d


        """
        if filter_name is None:
            filter_store = HDFStore(filter_data_fname, mode='r')
            available_filters = filter_store.keys()
            filter_store.close()
            print ("Available Filters\n"
                   "-----------------\n\n" + '\n'.join(available_filters))

        else:
            filter_store = HDFStore(filter_data_fname, mode='r')
            try:
                filter = filter_store[filter_name]
            except KeyError:
                filter_store.close()
                raise ValueError('Requested filter ({0}) does not exist'.format(
                    filter_name))
            finally:
                filter_store.close()
                
            if 'gemini' in filter_name:
                wavelength_unit = 'nm'
            elif 'bessell' in filter_name:
                wavelength_unit = 'angstrom'

            if wavelength_unit is None:
                raise ValueError('No "wavelength_unit" given and none '
                                 'autodetected')

            wavelength = filter.wavelength.values * u.Unit(wavelength_unit)

            return cls(wavelength, filter.transmission_lambda,
                       interpolation_kind=interpolation_kind)

    def __init__(self, wavelength, transmission_lambda, interpolation_kind='linear'):
        if not hasattr(wavelength, 'unit'):
            raise ValueError('the wavelength needs to be a astropy quantity')
        self.wavelength = wavelength
        self.transmission_lambda = transmission_lambda

        self.interpolation_object = interpolate.interp1d(self.wavelength,
                                                         self.transmission_lambda,
                                                         kind=interpolation_kind,
                                                         bounds_error=False,
                                                         fill_value=0.0)


    def __mul__(self, other):
        if not hasattr(other, 'flux') or not hasattr(other, 'wavelength'):
            raise ValueError('requiring a specutils.Spectrum1D-like object that'
                             'has attributes "flux" and "wavelength"')
        transmission = self.interpolate(other.wavelength)

        return Spectrum1D(transmission * other.flux, wcs=other.wcs)

    def __rmul__(self, other):
        return self.__mul__(other)

    @property
    def lambda_pivot(self):
        """
        Calculate the pivotal wavelength as defined in Bessell & Murphy 2012

        ..math::`$<f_\nu> = <f_\lambda>\frac{\lambda_\textrm{pivot}^2}{c}$`
        """

        return np.sqrt((np.trapz(self.transmission_lambda * self.wavelength)/
                (np.trapz(self.transmission_lambda / self.wavelength))))

    @property
    def zp_ab_f_lambda(self):
        return (self.zp_ab_f_nu * const.c / self.lambda_pivot**2).to(
            'erg/s/cm^2/Angstrom', u.spectral())

    @property
    def zp_ab_f_nu(self):
        return (3631 * u.Jy).to('erg/s/cm^2/Hz')



    @property
    def zp_vega_f_lambda(self):
        return (calculate_filter_f_lambda(get_vega(), self) /
                self.calculate_integral_wavelength())


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

    def calculate_integral_wavelength(self):
        """
        Calculate the Integral :math:`\integral
        :return:
        """

        return np.trapz(self.transmission_lambda, self.wavelength)

    def calculate_vega_magnitude(self, spectrum):
        __doc__ = calculate_vega_magnitude.__doc__
        return calculate_vega_magnitude(spectrum, self)


class FilterCurve(BaseFilterCurve):
    pass

class FilterSet(object):

    @classmethod
    def load_filter_set(cls, filter_set_names):
        """
        A list of filters to be loaded

        filter_set_names: list of strings
        """


    def __init__(self, filter_set, ):
        self.filter_set =