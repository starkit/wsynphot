import os, re
from tqdm.autonotebook import tqdm
# tqdm.autonotebook automatically chooses between console & notebook

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
