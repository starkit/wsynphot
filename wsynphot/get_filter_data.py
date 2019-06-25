import numpy as np
import pandas as pd
import requests
import io
from astropy import units as u

from astropy.io.votable import parse_single_table
# The VOTables fetched from SVO contain only single table element, thus parse_single_table

FLOAT_MAX = np.finfo(np.float64).max
SVO_MAIN_URL = 'http://svo2.cab.inta-csic.es/theory/fps/fps.php'

def get_filter_index(wavelength_eff_min=0, wavelength_eff_max=FLOAT_MAX):
    """Get master list (index) of all filters at SVO
    Optional parameters can be given to get filters data for specified
    Wavelength Eff. range from SVO

    Parameters
    ----------
    wavelength_eff_min : float, optional
        Minimum value of Wavelength Eff. (default is 0)
    wavelength_eff_max : float, optional
        Maximum value of Wavelength Eff. (default is a very large no. 
        FLOAT_MAX - maximum value of np.float64)

    Returns
    -------
    astropy.io.votable.tree.Table object
        Table element of the VOTable fetched from SVO (in response to query)
    """
    wavelength_eff_min = u.Quantity(wavelength_eff_min, u.angstrom)
    wavelength_eff_max = u.Quantity(wavelength_eff_max, u.angstrom)
    query = {'WavelengthEff_min': wavelength_eff_min.value,
             'WavelengthEff_max': wavelength_eff_max.value}    
    response = requests.get(SVO_MAIN_URL, params=query)
    response.raise_for_status()
    votable = io.BytesIO(response.content)
    try:
        return parse_single_table(votable)
    except IndexError:
        # If no table element found in VOTable
        raise ValueError('No filter found for requested Wavelength Eff. range')


def get_transmission_data(filter_id):
    """Get transmission data for the requested Filter ID from SVO

    Parameters
    ----------
    filter_id : str
        Filter ID in the format SVO specifies it: 'facilty/instrument.filter'

    Returns
    -------
    astropy.io.votable.tree.Table object
        Table element of the VOTable fetched from SVO (in response to query)
    """
    query = {'ID': filter_id}
    response = requests.get(SVO_MAIN_URL, params=query)
    response.raise_for_status()
    votable = io.BytesIO(response.content)
    try:
        return parse_single_table(votable)
    except IndexError:
        # If no table element found in VOTable
        raise ValueError('No filter found for requested Filter ID')


def get_filter_list(facility, instrument=None):
    """Get filters data for requested facilty and instrument from SVO

    Parameters
    ----------
    facility : str
        Facilty for filters
    instrument : str, optional
        Instrument for filters (default is None). 
        Leave empty if there are no instruments for specified facilty

    Returns
    -------
    astropy.io.votable.tree.Table object
        Table element of the VOTable fetched from SVO (in response to query)
    """
    query = {'Facility': facility, 
             'Instrument': instrument}
    response = requests.get(SVO_MAIN_URL, params=query)
    response.raise_for_status()
    votable = io.BytesIO(response.content)
    try:
        return parse_single_table(votable)
    except IndexError:
        # If no table element found in VOTable
        raise ValueError('No filter found for requested Facilty (and Instrument)')
