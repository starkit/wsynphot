# defining the base filter curve classes
from __future__ import print_function
import os

from scipy import interpolate
from wsynphot.spectrum1d import SKSpectrum1D as Spectrum1D
import pandas as pd
from wsynphot.data.base import FILTER_DATA_FPATH



from pandas import HDFStore
from astropy import units as u, constants as const

from astropy import utils
import numpy as np
from wsynphot.calibration import get_vega


def calculate_filter_flux_density(spectrum, filter):
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
    filter_flux_density = np.trapz(filtered_spectrum.flux * filtered_spectrum.wavelength,
                    filtered_spectrum.wavelength)
    return filter_flux_density

def calculate_vega_magnitude(spectrum, filter):
    filter_flux_density = calculate_filter_flux_density(spectrum, filter)
    wavelength_delta = filter.calculate_wavelength_delta()
    filtered_f_lambda = (filter_flux_density / wavelength_delta)

    zp_vega_f_lambda = filter.zp_vega_f_lambda

    return -2.5 * np.log10(filtered_f_lambda / zp_vega_f_lambda)



def calculate_ab_magnitude(spectrum, filter):
    filtered_f_lambda = (calculate_filter_flux_density(spectrum, filter) /
                         filter.calculate_wavelength_delta())

    return -2.5 * np.log10(filtered_f_lambda / filter.zp_ab_f_lambda)




def get_filter_index():
    """
    Get the index Dataframe for the Filters
    """
    if not os.path.exists(FILTER_DATA_FPATH):
        raise IOError('Filter Data does not exist at - {0} - please '
                      'download it by doing wsynphot.download_filter_data'
                      '()'.format(FILTER_DATA_FPATH))

    filter_index = pd.read_hdf(FILTER_DATA_FPATH, 'index').set_index('wsynphot_filter_id')
    return filter_index


def list_filters():
    """
    List available filter sets
    """

    return get_filter_index()

#To check whether both passed strings are float or not
def isFloat(str1,str2):
    try:
        float(str1)
        isFloat1=True
    except ValueError:
        isFloat1=False
    try:
        float(str2)
        isFloat2=True
    except ValueError:
        isFloat2=False
    return isFloat1 & isFloat2

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
    def load_filter(cls, filter_name=None, interpolation_kind='linear'):
        """

        Parameters
        ----------

        filter_name: str or None
            if None is provided will return a DataFrame of all filters

        wavelength_unit: str or astropy.units.Unit
            for some filtersets (e.g. gemini) this can be autodetected

        interpolation_kind: str
            see scipy.interpolation.interp1d


        """
        if not os.path.exists(FILTER_DATA_FPATH):
            raise IOError('Filter Data does not exist at - {0} - please '
                          'download it by doing wsynphot.download_filter_data'
                          '()'.format(FILTER_DATA_FPATH))
        if filter_name is None:
            filter_index = pd.read_hdf(FILTER_DATA_FPATH, 'index')
            return filter_index

        else:
            filter_store = HDFStore(FILTER_DATA_FPATH, mode='r')
            try:
                filter = filter_store[filter_name]
            except KeyError:
                filter_store.close()
                raise ValueError('Requested filter ({0}) does not exist'.format(
                    filter_name))
            finally:
                filter_store.close()

            #Cleaning filter data if string(dtype object) is present--------
            if filter.wavelength.dtype==np.dtype(object) or filter.transmission_lambda.dtype==np.dtype(object):
            	cleaningIndex=filter.apply(lambda row : isFloat(row['wavelength'],row['transmission_lambda']),axis = 1)
            	filter=filter[cleaningIndex].astype(float)
            	filter.reset_index(drop=True,inplace=True)

            wavelength_unit = 'angstrom'

            wavelength = filter.wavelength.values * u.Unit(wavelength_unit)

            return cls(wavelength, filter.transmission_lambda.values,
                       interpolation_kind=interpolation_kind,
                       filter_name=filter_name)

    def __init__(self, wavelength, transmission_lambda,
                 interpolation_kind='linear', filter_name=None):
        if not hasattr(wavelength, 'unit'):
            raise ValueError('the wavelength needs to be a astropy quantity')
        self.wavelength = wavelength
        self.transmission_lambda = transmission_lambda

        self.interpolation_object = interpolate.interp1d(self.wavelength,
                                                         self.transmission_lambda,
                                                         kind=interpolation_kind,
                                                         bounds_error=False,
                                                         fill_value=0.0)
        self.filter_name = filter_name


    def __mul__(self, other):
        if not hasattr(other, 'flux') or not hasattr(other, 'wavelength'):
            raise ValueError('requiring a specutils.Spectrum1D-like object that'
                             'has attributes "flux" and "wavelength"')

        #new_wavelength = np.union1d(other.wavelength.to(self.wavelength.unit).value,
        #                            self.wavelength.value) * self.wavelength.unit
        transmission = self.interpolate(other.wavelength)

        return Spectrum1D.from_array(other.wavelength, transmission * other.flux)

    def __rmul__(self, other):
        return self.__mul__(other)


    @utils.lazyproperty
    def lambda_pivot(self):
        """
        Calculate the pivotal wavelength as defined in Bessell & Murphy 2012

        .. math::

            \\lambda_\\textrm{pivot} = \\sqrt{
            \\frac{\\int S(\\lambda)\\lambda d\\lambda}{\\int \\frac{S(\\lambda)}{\\lambda}}}\\\\
            <f_\\nu> = <f_\\lambda>\\frac{\\lambda_\\textrm{pivot}^2}{c}
        """

        return np.sqrt((np.trapz(self.transmission_lambda * self.wavelength, self.wavelength)/
                (np.trapz(self.transmission_lambda / self.wavelength, self.wavelength))))

    @utils.lazyproperty
    def wavelength_start(self):
        return self.get_wavelength_start()


    @utils.lazyproperty
    def wavelength_end(self):
        return self.get_wavelength_end()

    @utils.lazyproperty
    def zp_ab_f_lambda(self):
        return (self.zp_ab_f_nu * const.c / self.lambda_pivot**2).to(
            'erg/s/cm^2/Angstrom', u.spectral())

    @utils.lazyproperty
    def zp_ab_f_nu(self):
        return (3631 * u.Jy).to('erg/s/cm^2/Hz')



    @utils.lazyproperty
    def zp_vega_f_lambda(self):
        return (calculate_filter_flux_density(get_vega(), self) /
                self.calculate_wavelength_delta())


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

    def _calculuate_flux_density(self, wavelength, flux):
        return _calculcate_filter_flux_density(flux, self)

    def calculate_flux_density(self, spectrum):
        return calculate_filter_flux_density(spectrum, self)


    def calculate_f_lambda(self, spectrum):
        return (self.calculate_flux_density(spectrum) /
                self.calculate_wavelength_delta())

    def calculate_wavelength_delta(self):
        """
        Calculate the Integral :math:`\integral
        :return:
        """

        return np.trapz(self.transmission_lambda * self.wavelength,
                        self.wavelength)

    def calculate_weighted_average_wavelength(self):
        """
        Calculate integral :math:`\\frac{\\int S(\\lambda) \\lambda d\\lambda}{\\int S(\\lambda) d\\lambda}`


        Returns
            : ~astropy.units.Quantity


        """

        return (np.trapz(self.transmission_lambda * self.wavelength,
                         self.wavelength) / self.calculate_wavelength_delta())

    def calculate_vega_magnitude(self, spectrum):
        __doc__ = calculate_vega_magnitude.__doc__
        return calculate_vega_magnitude(spectrum, self)

    def calculate_ab_magnitude(self, spectrum):
        __doc__ = calculate_ab_magnitude.__doc__
        return calculate_ab_magnitude(spectrum, self)

    def convert_ab_magnitude_to_f_lambda(self, mag):
        return 10**(-0.4*mag) * self.zp_ab_f_lambda

    def convert_vega_magnitude_to_f_lambda(self, mag):
        return 10**(-0.4*mag) * self.zp_vega_f_lambda

    def plot(self, ax, scale_max=None, make_label=True, plot_kwargs={},
             format_filter_name=None):
        if scale_max is not None:
            if hasattr(scale_max, 'unit'):
                scale_max = scale_max.value

            transmission = (self.transmission_lambda * scale_max
                            / self.transmission_lambda.max())
        else:
            transmission = self.transmission_lambda

        ax.plot(self.wavelength, transmission, **plot_kwargs)
        ax.set_xlabel('Wavelength [{0}]'.format(
            self.wavelength.unit.to_string(format='latex')))
        ax.set_xlabel('Transmission [1]')

        if make_label==True and self.filter_name is not None:
            if format_filter_name is not None:
                filter_name = format_filter_name(self.filter_name)
            else:
                filter_name = self.filter_name
            text_x = (self.lambda_pivot).value
            text_y = transmission.max()/2
            ax.text(text_x, text_y, filter_name,
                    horizontalalignment='center', verticalalignment='center',
                    bbox=dict(facecolor='white', alpha=0.5))

    def get_wavelength_start(self, threshold=0.01):
        norm_cum_sum = (np.cumsum(self.transmission_lambda)
                        / np.sum(self.transmission_lambda))
        return self.wavelength[norm_cum_sum.searchsorted(threshold)]

    def get_wavelength_end(self, threshold=0.01):
        norm_cum_sum = (np.cumsum(self.transmission_lambda)
                        / np.sum(self.transmission_lambda))
        return self.wavelength[norm_cum_sum.searchsorted(1 - threshold)]



class FilterCurve(BaseFilterCurve):
    def __repr__(self):
        if self.filter_name is None:
            filter_name = "{0:x}".format(self.__hash__())
        else:
            filter_name = self.filter_name
        return "FilterCurve <{0}>".format(filter_name)




class FilterSet(object):

    """
    A set of filters

    Parameters
    ----------

    filter_set: ~list
        a list of strings or a list of filters

    interpolation_kind: ~str
        scipy interpolaton kinds

    """
    def __init__(self, filter_set, interpolation_kind='linear'):

        if hasattr(filter_set[0], 'wavelength'):
            self.filter_set = filter_set
        else:
            self.filter_set = [FilterCurve.load_filter(filter_name,
                                              interpolation_kind=
                                              interpolation_kind)
                      for filter_name in filter_set]



    def __iter__(self):
        self.current_filter_idx = 0
        return self

    def __next__(self):
        try:
            item = self.filter_set[self.current_filter_idx]
        except IndexError:
            raise StopIteration

        self.current_filter_idx += 1
        return item
    next = __next__


    def __getitem__(self, item):
        return self.filter_set.__getitem__(item)

    def __repr__(self):
        return "<{0} \n{1}>".format(self.__class__.__name__,
                                    '\n'.join(
                                        [item.filter_name
                                         for item in self.filter_set]))


    @property
    def lambda_pivot(self):
        return u.Quantity([item.lambda_pivot for item in self])

    def calculate_f_lambda(self, spectrum):
        return u.Quantity(
            [item.calculate_f_lambda(spectrum) for item in self.filter_set])

    def calculate_ab_magnitudes(self, spectrum):
        mags = [item.calculate_ab_magnitude(spectrum)
                for item in self.filter_set]
        return mags

    def calculate_vega_magnitudes(self, spectrum):
        mags = [item.calculate_vega_magnitude(spectrum)
                for item in self.filter_set]
        return mags

    def convert_ab_magnitudes_to_f_lambda(self, magnitudes):
        if len(magnitudes) != len(self.filter_set):
            raise ValueError("Filter set and magnitudes need to have the same "
                             "number of items")
        f_lambdas = [filter.convert_ab_magnitude_to_f_lambda(mag)
                     for filter, mag in zip(self.filter_set, magnitudes)]
        return u.Quantity(f_lambdas)


    def convert_ab_magnitude_uncertainties_to_f_lambda_uncertainties(
            self, magnitudes, magnitude_uncertainties):

        if len(magnitudes) != len(self.filter_set):
            raise ValueError("Filter set and magnitudes need to have the same "
                             "number of items")
        f_lambda_positive_uncertainties = u.Quantity(
            [filter.convert_ab_magnitude_to_f_lambda(mag +  mag_uncertainty)
                     for filter, mag, mag_uncertainty in zip(
                self.filter_set, magnitudes, magnitude_uncertainties, )])

        f_lambda_negative_uncertainties = u.Quantity(
            [filter.convert_ab_magnitude_to_f_lambda(mag -  mag_uncertainty)
                     for filter, mag, mag_uncertainty in zip(
                self.filter_set, magnitudes, magnitude_uncertainties)])

        return np.abs(u.Quantity((f_lambda_positive_uncertainties,
                f_lambda_negative_uncertainties))
                      -  self.convert_ab_magnitudes_to_f_lambda(magnitudes))

    def convert_vega_magnitude_uncertainties_to_f_lambda_uncertainties(
            self, magnitudes, magnitude_uncertainties):

        if len(magnitudes) != len(self.filter_set):
            raise ValueError("Filter set and magnitudes need to have the same "
                             "number of items")
        f_lambda_positive_uncertainties = u.Quantity(
            [filter.convert_vega_magnitude_to_f_lambda(mag +  mag_uncertainty)
                     for filter, mag, mag_uncertainty in zip(
                self.filter_set, magnitudes, magnitude_uncertainties, )])

        f_lambda_negative_uncertainties = u.Quantity(
            [filter.convert_vega_magnitude_to_f_lambda(mag -  mag_uncertainty)
                     for filter, mag, mag_uncertainty in zip(
                self.filter_set, magnitudes, magnitude_uncertainties)])

        return np.abs(u.Quantity((f_lambda_positive_uncertainties,
                                  f_lambda_negative_uncertainties))
                      -  self.convert_vega_magnitudes_to_f_lambda(magnitudes))


    def convert_vega_magnitudes_to_f_lambda(self, magnitudes):
        if len(magnitudes) != len(self.filter_set):
            raise ValueError("Filter set and magnitudes need to have the same "
                             "number of items")
        f_lambdas = [filter.convert_vega_magnitude_to_f_lambda(mag)
                     for filter, mag in zip(self.filter_set, magnitudes)]
        return u.Quantity(f_lambdas)

    def plot_spectrum(self, spectrum, ax, make_labels=True,
                      spectrum_plot_kwargs={}, filter_plot_kwargs={},
                      filter_color_list=None, format_filter_name=None):
        """
        plot a spectrum with the given filters
        spectrum:
        ax:
        make_labels:
        :return:
        """
        ax.plot(spectrum.wavelength, spectrum.flux, **spectrum_plot_kwargs)
        for i, filter in enumerate(self.filter_set):
            filter_scale = filter.calculate_f_lambda(spectrum)
            if filter_color_list is not None:
                filter_plot_kwargs['color'] = filter_color_list[i]
            filter.plot(ax, scale_max=filter_scale, make_label=make_labels,
                        plot_kwargs=filter_plot_kwargs,
                        format_filter_name=format_filter_name)



class MagnitudeSet(FilterSet):
    def __init__(self, filter_set, magnitudes, magnitude_uncertainties=None,
                 interpolation_kind='linear'):
        super(MagnitudeSet, self).__init__(filter_set,
                                           interpolation_kind=
                                           interpolation_kind)
        self.magnitudes = np.array(magnitudes)
        self.magnitude_uncertainties = np.array(magnitude_uncertainties)

    def __repr__(self):
        mag_str = '{0} {1:.4f} +/- {2:.4f}'
        mag_data = []
        for i, filter in enumerate(self.filter_set):
            unc = (np.nan if self.magnitude_uncertainties is None
                   else self.magnitude_uncertainties[i])
            mag_data.append(mag_str.format(filter.filter_name,
                                           self.magnitudes[i], unc))

        return "<{0} \n{1}>".format(self.__class__.__name__,
                                    '\n'.join(mag_data))
