import os, re
import numpy as np

# tqdm.autonotebook automatically chooses between console & notebook
from tqdm.autonotebook import tqdm
from astropy.io.votable import parse_single_table

from wsynphot.io.get_filter_data import (get_filter_index,
    get_transmission_data)
from wsynphot.config import get_data_dir

CACHE_DIR = os.path.join(get_data_dir(), 'cached_SVO_FPS')
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)


def cache_as_votable(table, file_path):
    """Caches the passed table on disk as a VOTable.

    Parameters
    ----------
    table : astropy.table.Table
        Table to be cached 
    file_path : str
        Path where VOTable is to be saved 
    """
    if not file_path.endswith('.vot'):
        file_path += '.vot'

    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Write table as votable (overwrite for cases when file already exists)
    table.write(file_path, format='votable', overwrite=True)


def download_filter_data(cache_dir=CACHE_DIR):
    """Downloads the entire filter data (filter index and transmission data 
    of each filter) locally on disk as cache.

    Parameters
    ----------
    cache_dir : str, optional
        Path of the directory where downloaded data is to be cached 
    """
    # Get filter index and cache it
    print("Caching filter index ...")
    index_table = get_filter_index().to_table()
    cache_as_votable(index_table,
        os.path.join(cache_dir, 'index'))

    # Fetch filter_ids from index as an iterator decorated with progress bar
    print("Caching transmission data ...")
    filter_ids_pbar = tqdm(index_table['filterID'], desc='Filter ID',
        total=len(index_table))

    # Iterate over each filter_id in the generated iterator
    for filter_id in filter_ids_pbar:
        filter_id = filter_id.decode("utf-8")  # convert byte string to literal
        filter_ids_pbar.set_postfix_str(filter_id)

        # Get transmission data for a filter_id and cache it
        try:
            facility, instrument, filter_name = re.split('/|\.', filter_id)
            filter_table = get_transmission_data(filter_id).to_table()
            cache_as_votable(filter_table,
                os.path.join(cache_dir, facility, instrument, filter_name))
        except Exception as e:
            print('Data for Filter ID = {0} could not be downloaded due '
                'to:\n{1}'.format(filter_id, e))


def load_filter_index(cache_dir=CACHE_DIR):
    """Loads filter index from the cached filter data present on disk as a
    pandas dataframe.

    Parameters
    ----------
    cache_dir : str, optional
        Path of the directory where downloaded data is to be cached 

    Returns
    -------
    pandas.core.frame.DataFrame
        Filter index loaded as a dataframe
    """
    filter_index_loc = os.path.join(cache_dir, 'index.vot')
    error_msg = 'No filter index found'
    return df_from_votable(filter_index_loc, error_msg)


def load_transmission_data(filter_id, cache_dir=CACHE_DIR):
    """Loads transmission data for requested Filter ID from the cached filter 
    data present on disk as a pandas dataframe.

    Parameters
    ----------
    filter_id : str
        Filter ID in either wsynphot format: 'facilty/instrument/filter' 
        or SVO format: 'facilty/instrument.filter' (Can use '/' and '.' 
        interchangeably as delimiters)
    cache_dir : str, optional
        Path of the directory where downloaded data is to be cached 

    Returns
    -------
    pandas.core.frame.DataFrame
        Filter's transmission data loaded as a dataframe
    """
    facility, instrument, filter_name = re.split('/|\.', filter_id)
    transmission_data_loc = os.path.join(cache_dir, facility, instrument,
        '{0}.vot'.format(filter_name))
    error_msg = 'No filter found for requested Filter ID'
    return df_from_votable(transmission_data_loc, error_msg)


def df_from_votable(votable_path, error_msg):
    """Parses the passed VOTable to produce data in a usable table format as 
    pandas dataframe.

    Parameters
    ----------
    votable_path : str
        Path where VOTable to be used is stored. Make sure passed VOTable is 
        properly formatted, since this is "not" a general purpose function.
    error_msg : str
        Error message to be shown in case no VOTable exists for the passed
        path. Use this to make error message verbose in context of the 
        VOTable passed.

    Returns
    -------
    pandas.core.frame.DataFrame
        Parsed data as a dataframe
    """
    # When no such votable is present
    if not os.path.exists(votable_path):
        raise ValueError(error_msg)

    # Parse VOTable & convert it to Dataframe
    table = parse_single_table(votable_path).to_table()
    df = table.to_pandas()
    return byte_to_literal_strings(df)


def byte_to_literal_strings(dataframe):
    """Converts byte strings (if any) present in passed dataframe to literal
    strings and returns an improved dataframe.
    """
    # Select the str columns:
    str_df = dataframe.select_dtypes([np.object])
    
    if not str_df.empty:
        # Convert all of them into unicode strings
        str_df = str_df.stack().str.decode('utf-8').unstack()
        # Swap out converted cols with the original df cols
        for col in str_df:
            dataframe[col] = str_df[col]
    
    return dataframe
