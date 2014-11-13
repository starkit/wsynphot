from scipy import interpolate
from astropy import units as u
from specutils import Spectrum1D

class SpectralModel(object):
    """
    Spectral model


    """

    def __init__(self, wavelength_knots, flux_knots, wavelength=None, interpolation_kind=3):
        self.wavelength_knots = wavelength_knots
        self.flux_knots = flux_knots
        self._interpolation_kind = interpolation_kind

        if wavelength is None:
            self.wavelength = self.wavelength_knots
        else:
            self.wavelength = wavelength


    @property
    def wavelength(self):
        return self._wavelength

    @wavelength.setter
    def wavelength(self, wavelength):
        self._wavelength = wavelength
        self._flux = self.interpolate(self._wavelength, self.interpolation_kind)

    @property
    def interpolation_kind(self):
        return self._interpolation_kind

    @interpolation_kind.setter
    def interpolation_kind(self, interpolation_kind):
        self._interpolation_kind = interpolation_kind
        self._flux = self.interpolate(self.wavelength, self.interpolation_kind)



    @property
    def flux(self):
        return self._flux

    def interpolate(self, wavelength, interpolation_kind=3):
        """
        Interpolate the filter onto new wavelength grid

        Parameters
        ----------

        wavelength: ~astropy.units.Quantity
            wavelength grid to interpolate on

        """

        converted_wavelength = wavelength.to(self.wavelength.unit)
        interpolation_object = interpolate.interp1d(self.wavelength_knots,
                                                         self.flux_knots,
                                                         kind=interpolation_kind,
                                                         bounds_error=False,
                                                         fill_value=0.0)

        return interpolation_object(converted_wavelength) * self.flux_knots.unit





class MagnitudeSpectralModel(SpectralModel):
    """
    Generate a spectral model from magnitudes

    :param magnitude_set:
    :param magnitudes:
    :param magnitude_system:
    :param interpolation_kind:
    :param generate_end_points:
    :return:
    """

    def __init__(self, magnitude_set, magnitude_system='vega',
                        interpolation_kind=3, end_point_flux=0.0):

        wavelength = u.Quantity([item.lambda_pivot for item in magnitude_set])
        flux = getattr(magnitude_set,
                       'convert_{0}_magnitudes_to_f_lambda'.
                       format(magnitude_system))(magnitude_set.magnitudes)
        if magnitude_set.magnitude_uncertainties is not None:
            flux_err = getattr(magnitude_set,
                       'convert_{0}_magnitude_uncertainties_'
                       'to_f_lambda_uncertainties'.
                       format(magnitude_system))(
                magnitude_set.magnitudes,
                magnitude_set.magnitude_uncertainties)
        else:
            flux_err = None

        if end_point_flux is not None:
            start_filter = magnitude_set[0]
            start_wavelength = (start_filter.
                                wavelength[start_filter.transmission_lambda>0][0])

            end_filter = magnitude_set[-1]
            end_wavelength = (end_filter.
                                wavelength[end_filter.transmission_lambda>0][-1])

            wavelength = ([start_wavelength.to(wavelength.unit).value] +
                          wavelength.tolist() +
                          [end_wavelength.to(wavelength.unit).value]) * wavelength.unit
            flux = ([u.Quantity(end_point_flux, flux.unit).value] + flux.tolist()
                    + [u.Quantity(end_point_flux, flux.unit).value]) * flux.unit


        self.magnitude_set = magnitude_set
        self.flux_err = flux_err
        super(MagnitudeSpectralModel, self).__init__(wavelength, flux,
                                                     interpolation_kind=
                                                     interpolation_kind)




    def calculate_vega_magnitudes(self):
        return self.magnitude_set.calculate_vega_magnitudes(self)

    def calculate_ab_magnitudes(self):
        return self.magnitude_set.calculate_ab_magnitudes(self)

