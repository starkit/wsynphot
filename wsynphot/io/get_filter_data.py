import numpy as np
import pandas as pd
import requests
import io
import logging
from tqdm.autonotebook import tqdm
from requests.adapters import HTTPAdapter
from astropy import units as u
from astropy.io.votable import parse, parse_single_table
from astropy.table import vstack


# to enable retries when connection failures occur in making requests
session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=5))

logger = logging.getLogger(__name__)
FLOAT_MAX = np.finfo(np.float64).max
SVO_MAIN_URL = 'http://svo2.cab.inta-csic.es/theory/fps/fps.php'


def _get_entire_wavelength_range():
    """Get permissible range of Wavelength Eff. on SVO FPS

    Returns
    -------
    tuple of float
        (min, max) Wavelength Eff.
    """
    response = session.get(SVO_MAIN_URL, params={"FORMAT": "metadata"})
    response.raise_for_status()
    votable = parse(io.BytesIO(response.content))
    wave_min = votable.get_field_by_id("INPUT_WavelengthEff_min").values.min
    wave_max = votable.get_field_by_id("INPUT_WavelengthEff_max").values.max
    return (wave_min, wave_max)


def data_from_svo(query, error_msg='No data found for requested query'):
    """Get data in response to the query send to SVO FPS

    Parameters
    ----------
    query : dict
        Used to create a HTTP query string i.e. send to SVO FPS to get data.
        In dictionary, specify keys as search parameters (str) and 
        values as required. List of search parameters can be found at 
        http://svo2.cab.inta-csic.es/theory/fps/fps.php?FORMAT=metadata
    error_msg : str, optional
        Error message to be shown in case no table element found in the
        responded VOTable. Use this to make error message verbose in context 
        of the query made (default is 'No data found for requested query')

    Returns
    -------
    astropy.io.votable.tree.Table object
        Table element of the VOTable fetched from SVO (in response to query)
    """
    response = session.get(SVO_MAIN_URL, params=query)
    response.raise_for_status()
    votable = io.BytesIO(response.content)
    try:
        return parse_single_table(votable)
    except IndexError:
        # If no table element found in VOTable
        raise ValueError(error_msg)


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
    error_msg = 'No filter found for requested Wavelength Eff. range'
    return data_from_svo(query, error_msg)


def get_filter_index_in_batches(n_batches=25):
    """Get master list (index) of all filters at SVO in batches.

    The batches are bins of the entire wavelength effective range (in Angstrom).
    For each batch, filters present in that wavelength bin are fetched. This
    is helpful because fetching all filters at once will take so much time
    without giving any feedback to user.

    Parameters
    ----------
    n_batches : int, default: 25, optional
        Number of batches. If not required don't change it otherwise it may
        affect binning of wavelength range adversely.

    Returns
    -------
    astropy.table.Table
        VOTable fetched from SVO (in response to query)
    """
    wave_min, wave_max = _get_entire_wavelength_range()

    # SVO filters distribution across entire wavelength range is highly
    # skewed to left (but that left edge is 1e3), hence log spacing as follows
    wavelength_eff_bins = np.logspace(3, np.log10(wave_max), n_batches+1)
    # since very less filters in wave_min to 1e3 range
    wavelength_eff_bins[0] = wave_min

    batches_pbar = tqdm(range(n_batches), desc="Batch No.")

    for i in batches_pbar:
        query = {'WavelengthEff_min': wavelength_eff_bins[i],
                 'WavelengthEff_max': wavelength_eff_bins[i+1]}
        error_msg = f'No filter found for Wavelength Eff. range: {wavelength_eff_bins[i]:.2f} - {wavelength_eff_bins[i+1]:.2f}'

        try:
            data_fetched = data_from_svo(query, error_msg).to_table()
            if i == 0:
                data = data_fetched
            else:
                data = vstack([data, data_fetched], join_type='exact')
            num_filters_fetched = len(data_fetched)
        except ValueError:
            num_filters_fetched = 0

        batches_pbar.set_postfix_str(
            f"{num_filters_fetched} filters fetched in ({wavelength_eff_bins[i]:.2f}, "
            f"{wavelength_eff_bins[i+1]:.2f}) AA wavelength range"
        )

    logger.info(f"Total {len(data)} filters fetched in "
                f"({wavelength_eff_bins[0]:.2f}, {wavelength_eff_bins[-1]:.2f}) AA wavelength range")
    return data


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
    error_msg = 'No filter found for requested Filter ID'
    return data_from_svo(query, error_msg)


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
    error_msg = 'No filter found for requested Facilty (and Instrument)'
    return data_from_svo(query, error_msg)
