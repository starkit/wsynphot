# defining the base filter curve classes

import os
import logging
from scipy import interpolate
from wsynphot.spectrum1d import SKSpectrum1D as Spectrum1D
import pandas as pd
from wsynphot.io.cache_filters import DetectorType, load_local_filters_index, load_transmission_data



from astropy import units as u, constants as const

from astropy import utils
import numpy as np
from wsynphot.calibration import get_vega_calibration_spectrum
logger = logging.getLogger(__name__)

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
    if filter.detector_type == DetectorType.PHOTON_COUNTER:
        filter_flux_density = np.trapz(filtered_spectrum.flux * filtered_spectrum.wavelength,
                    filtered_spectrum.wavelength)
    else:  # DetectorType.ENERGY_COUNTER
        filter_flux_density = np.trapz(filtered_spectrum.flux,
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


def list_filters():
    """
    List available filters
    """
    logger.info("Following filters present in your cache directory are "
                "available to use (to see all filters you can download from "
                "SVO, use wsynphot.io.cache_filters.load_svo_filters_index()):")
    return pd.Series(load_local_filters_index(), name="Filter ID")


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
    def load_filter(cls, filter_id=None, interpolation_kind='linear', vega_fpath=None):
        """

        Parameters
        ----------

        filter_id: str or None
            if None is provided will return a DataFrame of all filters

        interpolation_kind: str
            see scipy.interpolation.interp1d
        
        vega_fpath: str, optional
            Path of Vega calibration file to be used for calculating vega magnitudes
        """
        if filter_id is None:
            return list_filters()

        else:
            transmission_data, detector_type = load_transmission_data(
                filter_id)
            
            wavelength_unit = 'angstrom'

            wavelength = transmission_data['Wavelength'].values * u.Unit(wavelength_unit)

            return cls(wavelength, transmission_data['Transmission'].values, detector_type,
                       interpolation_kind=interpolation_kind,
                       filter_id=filter_id, vega_fpath=vega_fpath)

    def __init__(self, wavelength, transmission_lambda, detector_type,
                 interpolation_kind='linear', filter_id=None, vega_fpath=None):
        if not hasattr(wavelength, 'unit'):
            raise ValueError('the wavelength needs to be a astropy quantity')
        self.wavelength = wavelength
        self.transmission_lambda = transmission_lambda
        self.detector_type = detector_type

        self.interpolation_object = interpolate.interp1d(self.wavelength,
                                                         self.transmission_lambda,
                                                         kind=interpolation_kind,
                                                         bounds_error=False,
                                                         fill_value=0.0)
        self.filter_id = filter_id
        self.vega_fpath = vega_fpath


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
        Calculate the pivotal wavelength as defined as equation A16 in 
        Bessell & Murphy 2012 (https://arxiv.org/abs/1112.2698)

        .. math::

            \\lambda_\\textrm{pivot} = \\sqrt{
            \\frac{\\int S(\\lambda)\\lambda d\\lambda}{\\int \\frac{S(\\lambda)}{\\lambda}}}\\\\
            <f_\\nu> = <f_\\lambda>\\frac{\\lambda_\\textrm{pivot}^2}{c}
        """
        if self.detector_type == DetectorType.PHOTON_COUNTER:
            return np.sqrt(
                np.trapz(self.transmission_lambda * self.wavelength, self.wavelength)/
                np.trapz(self.transmission_lambda / self.wavelength, self.wavelength)
                )
        else:  # DetectorType.ENERGY_COUNTER
            # substituting eq A9 in eq A16
            return np.sqrt(
                np.trapz(self.transmission_lambda, self.wavelength)/
                np.trapz(self.transmission_lambda / (self.wavelength**2), self.wavelength)
                )
        

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
        return (calculate_filter_flux_density(
            get_vega_calibration_spectrum(self.vega_fpath), self
        ) / self.calculate_wavelength_delta())


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
        if self.detector_type == DetectorType.PHOTON_COUNTER:
            return np.trapz(self.transmission_lambda * self.wavelength,
                            self.wavelength)
        else:  # DetectorType.ENERGY_COUNTER
            return np.trapz(self.transmission_lambda,
                            self.wavelength)

    def calculate_weighted_average_wavelength(self):
        """
        Calculate integral defined as equation A14 in Bessell & Murphy 2012 
        (https://arxiv.org/abs/1112.2698)
        
        :math:`\\frac{\\int S(\\lambda) \\lambda d\\lambda}{\\int S(\\lambda) d\\lambda}`


        Returns
            : ~astropy.units.Quantity


        """
        if self.detector_type == DetectorType.PHOTON_COUNTER:
            return (self.calculate_wavelength_delta() /
                    np.trapz(self.transmission_lambda, self.wavelength))
        else:  # DetectorType.ENERGY_COUNTER
            # substituting eq A9 in eq A14
            return (self.calculate_wavelength_delta() /
                    np.trapz(self.transmission_lambda / self.wavelength, self.wavelength))
        

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
             format_filter_id=None):
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
        ax.set_ylabel('Transmission [1]')

        if make_label==True and self.filter_id is not None:
            if format_filter_id is not None:
                filter_id = format_filter_id(self.filter_id)
            else:
                filter_id = self.filter_id
            text_x = (self.lambda_pivot).value
            text_y = transmission.max()/2
            ax.text(text_x, text_y, filter_id,
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
        if self.filter_id is None:
            filter_id = "{0:x}".format(self.__hash__())
        else:
            filter_id = self.filter_id
        return "FilterCurve <{0}>".format(filter_id)




class FilterSet(object):

    """
    A set of filters

    Parameters
    ----------

    filter_set: ~list
        a list of strings or a list of filters

    interpolation_kind: ~str
        scipy interpolaton kinds

    vega_fpath: str, optional
        Path of Vega calibration file to be used for calculating vega magnitudes

    """

    def __init__(self, filter_set, interpolation_kind='linear', vega_fpath=None):

        if hasattr(filter_set[0], 'wavelength'):
            self.filter_set = filter_set
        else:
            self.filter_set = [FilterCurve.load_filter(filter_id,
                                                       interpolation_kind=interpolation_kind,
                                                       vega_fpath=vega_fpath)
                               for filter_id in filter_set]



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
                                        [item.filter_id
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
                      filter_color_list=None, format_filter_id=None):
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
                        format_filter_id=format_filter_id)



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
            mag_data.append(mag_str.format(filter.filter_id,
                                           self.magnitudes[i], unc))

        return "<{0} \n{1}>".format(self.__class__.__name__,
                                    '\n'.join(mag_data))
