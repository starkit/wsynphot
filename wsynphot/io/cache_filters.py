import os
import re
import numpy as np
import logging
from enum import IntEnum
from glob import glob

# tqdm.autonotebook automatically chooses between console & notebook
from tqdm.autonotebook import tqdm
from astropy.io.votable import parse, parse_single_table

from wsynphot.io.get_filter_data import (get_filter_index_in_batches,
                                         get_transmission_data)
from wsynphot.config import get_cache_dir, set_cache_updation_date

CACHE_DIR = get_cache_dir()
logger = logging.getLogger(__name__)


class DetectorType(IntEnum):
    ENERGY_COUNTER = 0
    PHOTON_COUNTER = 1


def download_filter_data(filter_ids=None, cache_dir=CACHE_DIR):
    """Downloads the transmission data of each filter passed, locally on disk as 
    cache. If filter_ids not specified, it will download transmission data of all
    filters (~10k+) available at SVO.

    Parameters
    ----------
    filter_ids: iterable
        Iterable object containing Filter IDs as str in either wsynphot format: 
        'facilty/instrument/filter' or SVO format: 'facilty/instrument.filter' 
        (Can use '/' and '.' interchangeably as delimiters)
    cache_dir : str, optional
        Path of the directory where downloaded data is to be cached
    
    Returns
    -------
    list of str
        List of filter IDs for which data could not be downloaded 
    """
    download_all_mode = False

    if filter_ids is None:
        download_all_mode = True
        logger.info("Fetching index of all filters at SVO (in batches) ...")
        download_svo_filters_index(cache_dir)

        svo_filters_index = load_svo_filters_index(cache_dir)
        filter_ids = svo_filters_index["filterID"]

    # Download transmission data for each filter
    logger.info("Caching transmission data ...")
    failed_filter_ids = iterative_download_transmission_data(
        filter_ids, cache_dir)

    if download_all_mode and len(failed_filter_ids) == 0:
        # Save in config that all filter are up-to-date
        set_cache_updation_date()

    return failed_filter_ids


def download_svo_filters_index(cache_dir=CACHE_DIR):
    """Downloads index of all filters present at SVO in the cache.

    Parameters
    ----------
    cache_dir : str, optional
        Path of the directory where downloaded data is to be cached 
    """
    index_table = get_filter_index_in_batches()
    fpath = os.path.join(cache_dir, 'svo_index.vot')
    index_table.write(fpath, format='votable', overwrite=True)


def download_transmission_data(filter_id, cache_dir=CACHE_DIR):
    """Downloads transmission data for the requested filter ID systematically  
    on disk as cache (in facility/instrument/ directory).

    Parameters
    ----------
    filter_id : str
        Filter ID in either wsynphot format: 'facilty/instrument/filter' 
        or SVO format: 'facilty/instrument.filter' (Can use '/' and '.' 
        interchangeably as delimiters)
    cache_dir : str, optional
        Path of the directory where downloaded data is to be cached 
    """
    facility, instrument, filter_name = re.split('/|\.', filter_id)
    # Convert filter_id in SVO format to get transmission data from SVO
    svo_filter_id = '{0}/{1}.{2}'.format(facility, instrument, filter_name)
    filter_votable = get_transmission_data(svo_filter_id)

    dir_path = os.path.join(cache_dir, facility, instrument)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    filter_votable.to_xml(os.path.join(dir_path, f"{filter_name}.vot"))


def iterative_download_transmission_data(filter_ids, cache_dir=CACHE_DIR):
    """Iteratively downloads transmission data for the passed filter IDs 
    iterator, by internally calling download_transmission_data(). It also 
    displays a progress bar with necessary information for the filters being 
    downloaded.

    Parameters
    ----------
    filter_ids: iterable
        Iterable object containing Filter IDs as str in either wsynphot format: 
        'facilty/instrument/filter' or SVO format: 'facilty/instrument.filter' 
        (Can use '/' and '.' interchangeably as delimiters)
    cache_dir : str, optional
        Path of the directory where downloaded data is to be cached

    Returns
    -------
    list of str
        List of filter IDs for which data could not be downloaded 
    """
    # Decorate the iterator with progress bar
    filter_ids_pbar = tqdm(filter_ids, desc='Filter ID', total=len(filter_ids))
    failed_filter_ids = []

    # Iterate over each filter_id and download transmission data
    for filter_id in filter_ids_pbar:
        if isinstance(filter_id, bytes):  # treat byte string
            filter_id = filter_id.decode("utf-8")

        filter_ids_pbar.set_postfix_str(filter_id)

        try:
            download_transmission_data(filter_id, cache_dir)
        except Exception as e:
            failed_filter_ids.append(filter_id)
            logger.error('Data for filter ID = {0} could not be downloaded '
                         'due to:\n{1}'.format(filter_id, e))

    return failed_filter_ids


def update_filter_data(cache_dir=CACHE_DIR):
    """Makes the cached filter data same as SVO by downloading new filters 
    & removing outdated filters. 
    
    You need not to use this if you only want to keep limited number of
    filters of your choice (over all filters i.e. ~10k+) in the cache.

    Parameters
    ----------
    cache_dir : str, optional
        Path of the directory where cached filter data is present 

    Returns
    -------
    bool
        True if cache got updated, otherwise False for the case when cache is 
        already up-to-date
    """
    # Obtain all filter IDs from cache as old_filters
    old_index = load_local_filters_index(cache_dir)
    old_filters = np.array(old_index)

    # Obtain all filter IDs from SVO FPS as new_filters
    logger.info("Fetching latest index of all filters at SVO (in batches) ...")
    download_svo_filters_index(cache_dir)
    new_index = load_svo_filters_index(cache_dir)
    new_filters = new_index["filterID"].to_numpy()

    # Check whether there is need to update
    if np.array_equal(old_filters, new_filters):
        logger.info('Filter data is already up-to-date!')
        set_cache_updation_date()
        return False

    # Iterate & remove (old_filters - new_filters) from cache
    filters_to_remove = np.setdiff1d(old_filters, new_filters)
    logger.info("Removing outdated filters ...")
    for filter_id in filters_to_remove:
        facility, instrument, filter_name = re.split('/|\.', filter_id)
        filter_file = os.path.join(cache_dir, facility, instrument,
                                   '{0}.vot'.format(filter_name))
        if os.path.exists(filter_file):
            os.remove(filter_file)
    remove_empty_dirs(cache_dir)

    # Iterate & download (new_filters - old_filters) into cache
    filters_to_add = np.setdiff1d(new_filters, old_filters)
    logger.info("Caching new filters ...")
    iterative_download_transmission_data(filters_to_add, cache_dir)

    # Save in config that all filters were updated successfully
    set_cache_updation_date()
    return True


def load_local_filters_index(cache_dir=CACHE_DIR):
    """Loads index of all filters present on disk.

    Parameters
    ----------
    cache_dir : str, optional
        Path of the directory where downloaded data was cached 

    Returns
    -------
    list of str
        Filter IDs of filters present in the cache
    """
    # create index from all filters present in cache (over reading from a file)
    # so that index is always in sync with what is present on disk
    local_filters_index = [os.path.splitext(os.path.relpath(path, cache_dir))[0]
                           for path in glob(f"{cache_dir}/*/*/*.vot")]

    # TODO: Return a dataframe consisting of filter id and filter properties
    # (by reading params from filters' votable files)
    return local_filters_index


def load_svo_filters_index(cache_dir=CACHE_DIR):
    """Loads index of all filters at SVO if present on disk, as a
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
    svo_filter_index_loc = os.path.join(cache_dir, 'svo_index.vot')

    # When no index votable is present
    if not os.path.exists(svo_filter_index_loc):
        raise IOError('SVO filter index does not exist in the cache directory: '
                      '{0}\nMake sure you have already downloaded it by using '
                      'wsynphot.io.cache_filters.download_svo_filters_index()'.format(cache_dir))

    return df_from_votable(svo_filter_index_loc)


def load_transmission_data(filter_id, cache_dir=CACHE_DIR):
    """Loads transmission data (and metadata) of the requested filter from the 
    cached filter data present on disk.

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

    DetectorType(Enum)
        Filter's detector type: energy counter or photon counter
    """
    facility, instrument, filter_name = re.split('/|\.', filter_id)
    transmission_data_loc = os.path.join(cache_dir, facility, instrument,
                                         '{0}.vot'.format(filter_name))

    # When no such filter votable is present
    if not os.path.exists(transmission_data_loc):
        raise IOError("No data found in the cache directory ({0}) for the "
                      "requested filter ID: {1}. Use download_transmission_data() "
                      "to download it to the cache.".format(cache_dir, filter_id))

    transmission_df = df_from_votable(transmission_data_loc)
    detector_type = detector_type_from_votable(transmission_data_loc)

    return transmission_df, detector_type


def df_from_votable(votable_path):
    """Parses the passed VOTable to produce data in a usable table format as 
    pandas dataframe.

    Parameters
    ----------
    votable_path : str
        Path where VOTable to be used is stored. Make sure passed VOTable is 
        properly formatted, since this is "not" a general purpose function.

    Returns
    -------
    pandas.core.frame.DataFrame
        Parsed data as a dataframe
    """
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


def remove_empty_dirs(root_dir):
    """Removes empty directories if present in the passed directory"""
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for dirname in dirs:
            dirpath = os.path.join(root, dirname)
            if not os.listdir(dirpath):  # check whether the dir is empty
                os.rmdir(dirpath)


def detector_type_from_votable(votable_path):
    """Parses the passed VOTable to fetch detector type.

    Parameters
    ----------
    votable_path : str
        Path where VOTable to be used is stored. Make sure passed VOTable is 
        properly formatted, since this is "not" a general purpose function.

    Returns
    -------
    DetectorType(IntEnum)
    """
    votable = parse(votable_path)
    detector_type = votable.get_field_by_id("DetectorType").value
    return DetectorType(int(detector_type))
