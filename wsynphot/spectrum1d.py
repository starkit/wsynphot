import numpy as np
from astropy import constants as const
from astropy import units as u
from starkit.fix_spectrum1d import SKSpectrum1D


# TODO: this can eventually be replaced with an astropy3+ function
# from astropy.modeling import blackbody_lambda
#
# this version is adapted from astropy.modeling.blackbody
def blackbody_lambda(wavelength, temperature):
    """
    Calculate the blackbody spectral density per unit wavelength.

    Parameters
    ----------
    wavelength : `~astropy.units.Quantity`
        Wavelength array to evaluate on.

    temperature : `~astropy.units.Quantity`
        Blackbody temperature.
    """

    # Convert to units for calculations, also force double precision
    with u.add_enabled_equivalencies(u.spectral() + u.temperature()):
        freq = u.Quantity(wavelength, u.Hz, dtype=np.float64)
        temp = u.Quantity(temperature, u.K, dtype=np.float64)

    log_boltz = const.h * freq / (const.k_B * temp)
    boltzm1 = np.expm1(log_boltz)

    bb_nu = (2.0 * const.h * freq ** 3 / (const.c ** 2 * boltzm1))

    flam = u.erg / (u.cm**2 * u.s * u.AA)
    flux = bb_nu.to(flam, u.spectral_density(wavelength))

    return flux / u.sr  # Add per steradian to output flux unit


def blackbody1d(temperature, radius, distance=10*u.pc,
                lambda_min=2000, lambda_max=10000, dlambda=1):
    """
    One dimensional blackbody spectrum.

    Parameters
    ----------
    temperature : float or `~astropy.units.Quantity`
        Blackbody temperature.
        If not a Quantity, it is assumed to be in Kelvin.

    radius : `~astropy.units.Quantity`
        Radius of spherical blackbody.
        Must be a Quantity.

    distance : `~astropy.units.Quantity`
        Distance of blackbody source.
        Must be a Quantity.
        Default is 10 pc so absolute and apparent magnitudes will be the same.

    lambda_min : float
        Minimum wavelength for spectrum (in Angstroms).

    lambda_max : float
        Maximum wavelength for spectrum (in Angstroms).

    dlambda : float
        Wavelength interval for spectrum (in Angstroms).


    Returns
    -------
    bb : `~starkit.fix_spectrum1d.SKSpectrum1D`
        Blackbody spectrum.
    """

    if not hasattr(radius, 'unit'):
        raise ValueError("radius needs to be a quantity (e.g., 1 * u.cm)")

    if not hasattr(distance, 'unit'):
        raise ValueError("distance needs to be a quantity (e.g., 1 * u.pc)")

    wavelength = np.arange(lambda_min, lambda_max, dlambda) * u.AA

    # the factor of pi sr is from the angular integral
    flux = np.pi * u.sr * (radius/distance)**2 * blackbody_lambda(wavelength, temperature)

    # theoretical quantity has no uncertainty
    uncertainty = np.zeros_like(flux)

    bb = SKSpectrum1D.from_array(wavelength, flux, uncertainty)

    return bb
